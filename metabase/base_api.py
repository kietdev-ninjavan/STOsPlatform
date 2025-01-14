import logging
import time
from typing import Any

import requests
from django.core.cache import cache
from django.utils import timezone

from core.patterns import SingletonMeta
from google_wrapper.models import ServiceAccount
from google_wrapper.services import GoogleSheetService, GoogleChatService
from google_wrapper.utils import get_service_account
from google_wrapper.utils.card_builder import CardBuilder
from google_wrapper.utils.card_builder import widgets as W
from google_wrapper.utils.card_builder.elements import CardHeader, Section
from stos.utils import configs


class SessionManager(metaclass=SingletonMeta):
    """
    Singleton class to manage authorization tokens, ensuring only one instance exists.
    Tokens are cached and refreshed as needed, with expiration checks and automatic updates.
    """

    SESSION_CACHE_KEY = "metabase_session"
    SESSION_CACHE_TIMEOUT = 60 * 60 * 24 * 7  # 7 days

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the SessionManager with a logger and token lock for thread safety.
        """
        self.__logger = logger
        self.__configs = configs
        self.__webhook_url = self.__configs.get('ROOT_NOTIFICATION_WEBHOOK')

    @staticmethod
    def _build_card(header: str, message: str):
        """
        Build a Google Chat notification card for session-related messages.

        Args:
            header (str): Header for the card.
            message (str): Message to be displayed on the card.

        Returns:
            dict: A card representation for Google Chat.
        """
        card_builder = CardBuilder()
        card_header = CardHeader()
        card_header.title = "Metabase Session Manager"
        card_header.subtitle = timezone.now().strftime('%d/%m/%Y %H:%M:%S')
        card_builder.set_header(card_header)

        section = Section()
        section.header = header
        section.add_widget(W.TextParagraph(message))
        card_builder.add_section(section)

        return card_builder.card

    def _get_session_from_gsheet(self) -> str:
        """
        Retrieve the session id from Google Sheets.

        Returns:
            str: The session id retrieved from the Google Sheet.
        """
        try:
            service_account = get_service_account(configs.get('GSA_SYSTEM'))
            gsheets_service = GoogleSheetService(
                service_account=service_account,
                spreadsheet_id=configs.get('CONFIGS_SPREADSHEET_ID'),
                logger=self.__logger
            )
            return gsheets_service.read_cell(
                cell=configs.get('MTB_SESSION_CELL'),
                worksheet=configs.get('MTB_SESSION_WORKSHEET_ID', cast=int)
            )
        except ServiceAccount.DoesNotExist:
            self.__logger.error('Service Account not found.')
            raise
        except Exception as error:
            self.__logger.error(f'Error reading session ID from Google Sheet: {error}')
            raise

    def session_is_alive(self) -> bool:
        """
        Check if the current session alive.

        Returns:
            bool: True if session is alive, False otherwise.
        """
        session_id = self.session
        if not session_id:
            self.__logger.info("No session ID found in cache, assuming not alive.")
            return False

        url = "https://metabase.ninjavan.co/api/user/current"
        session = requests.Session()
        session.headers.update({'X-Metabase-Session': session_id})

        try:
            response = session.get(url)
            if response.status_code == 200:
                self.__logger.info("Session ID is alive.")
                return True
            if response.status_code == 401:
                self.__logger.info("Session ID has expired.")
                return False
        except requests.RequestException as error:
            self.__logger.error(f"Error checking session ID expiration: {error}")
            return False
        finally:
            session.close()

    def update_session(self) -> None:
        """
        Update the session by retrieving it from Google Sheets.
        Retry until a valid session is fetched and cached.
        """
        chat_service = GoogleChatService(logger=self.__logger)
        card = self._build_card(
            header='<font color="#6953cc">Metabase Session ID Expired</font>',
            message=f'Session ID: "{self.session}".\nPlease update token in Google Sheet.\nRetrying in 60 seconds.'
        )
        chat_service.webhook_send(self.__webhook_url, card=card)
        time.sleep(60)
        try:
            self.__logger.info('Attempting to update session...')
            new_session = self._get_session_from_gsheet()
            if new_session != self.session:
                cache.set(self.SESSION_CACHE_KEY, new_session, timeout=self.SESSION_CACHE_TIMEOUT)
                self.__logger.info('Session ID successfully updated and cached.')

                card = self._build_card(
                    header='<font color="#e5ea60">Metabase Session Updated</font>',
                    message=f'Updated session ID: "{new_session}".'
                )
                chat_service.webhook_send(self.__webhook_url, card=card)
        except Exception as error:
            self.__logger.error(f'Error updating session ID: {error}')
            raise error

    @staticmethod
    def auto_update_session(func):
        """
        Decorator to automatically update the session if expired before invoking the function.

        Args:
            func (callable): The function to decorate.

        Returns:
            callable: The wrapped function.
        """

        def wrapper(self, *args, **kwargs):
            # Check if the token has expired using the token manager instance
            while not self.session_manager.session_is_alive():
                self.session_manager.update_session()  # Access via session_manager
            return func(self, *args, **kwargs)

        return wrapper

    @property
    def session(self) -> str:
        """
        Retrieve the current token from cache.

        Returns:
            str: Cached session or None if not set.
        """
        return cache.get(self.SESSION_CACHE_KEY)

class BaseAPI:
    """
    A base class for making API requests.

    Attributes:
        endpoint (str): The API endpoint.
        session (requests.Session): A session object for making requests.
    """

    def __init__(self, endpoint: str, logger):
        """
        Initializes the BaseAPI class with the given API key and endpoint.

        Args:
            session (str): The API key for authorization.
            endpoint (str): The API endpoint.
        """
        self.__logger = logger
        self.__endpoint = endpoint
        self.session = requests.Session()
        self.session_manager = SessionManager(logger=self.__logger)

    def _set_session_headers(self):
        """Sets the authorization header for the session."""
        self.session.headers.update({
            'X-Metabase-Session': self.session_manager.session
        })

    @staticmethod
    def _process_response(response: requests.Response):
        """
        Processes the API response.

        Args:
            response (requests.Response): The response from the API request.

        Returns:
            tuple: A tuple containing the status code and the response data.
        """
        if response.status_code == 204:
            return response.status_code, {}

        if response.content:
            return response.status_code, response.json()

        return response.status_code, {}
    
    @SessionManager.auto_update_session
    def make_request(self, url: str, method: str = 'GET', payload: dict = None, files: dict = None):
        """
        Makes an API request with the given parameters.

        Args:
            url (str): The URL for the API request.
            method (str, optional): The HTTP method to use (default is 'GET').
            payload (dict, optional): The payload for the request (default is None).
            files (dict, optional): The files for the request (default is None).

        Returns:
            tuple: A tuple containing the status code and the response data.
        """
        self._set_session_headers()

        try:
            self.__logger.debug(f"Payload: {payload}")
            response = self.session.request(method, url, json=payload, files=files)
            self.__logger.info(f"{response.url} {response.request.method} {response.status_code}")

            response.raise_for_status()

            return self._process_response(response)

        except requests.exceptions.HTTPError as http_error:
            self.__logger.error(f"HTTP error occurred: {http_error}")
            return http_error.response.status_code, http_error.response.json()

        except requests.exceptions.RequestException as req_error:
            self.__logger.error(f"Request failed due to error: {req_error}")
            return 500, {'error': 'Request failed due to error'}