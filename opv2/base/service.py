import logging
import time
from abc import ABC
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


class TokenManager(metaclass=SingletonMeta):
    """
    Singleton class to manage authorization tokens, ensuring only one instance exists.
    Tokens are cached and refreshed as needed, with expiration checks and automatic updates.
    """

    TOKEN_CACHE_KEY = "opv2_auth_token"
    TOKEN_CACHE_TIMEOUT = 60 * 60 * 26  # 26 hours

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the TokenManager with a logger and token lock for thread safety.
        """
        self.__logger = logger
        self.__configs = configs
        self.__webhook_url = self.__configs.get('ROOT_NOTIFICATION_WEBHOOK')

    @staticmethod
    def _build_card(header: str, message: str):
        """
        Build a Google Chat notification card for token-related messages.

        Args:
            header (str): Header for the card.
            message (str): Message to be displayed on the card.

        Returns:
            dict: A card representation for Google Chat.
        """
        card_builder = CardBuilder()
        card_header = CardHeader()
        card_header.title = "OPv2 Token Manager"
        card_header.subtitle = timezone.now().strftime('%d/%m/%Y %H:%M:%S')
        card_builder.set_header(card_header)

        section = Section()
        section.header = header
        section.add_widget(W.TextParagraph(message))
        card_builder.add_section(section)

        return card_builder.card

    def _get_token_from_gsheet(self) -> str:
        """
        Retrieve the token from Google Sheets.

        Returns:
            str: The token retrieved from the Google Sheet.
        """
        try:
            service_account = get_service_account(configs.get('GSA_SYSTEM'))
            gsheets_service = GoogleSheetService(
                service_account=service_account,
                spreadsheet_id=configs.get('CONFIGS_SPREADSHEET_ID'),
                logger=self.__logger
            )
            return gsheets_service.read_cell(
                cell=configs.get('OPV2_TOKEN_CELL_TOKEN'),
                worksheet=configs.get('OPV2_TOKEN_WORKSHEET_ID', cast=int)
            )
        except ServiceAccount.DoesNotExist:
            self.__logger.error('Service Account not found.')
            raise
        except Exception as error:
            self.__logger.error(f'Error reading token from Google Sheet: {error}')
            raise

    def token_is_expired(self) -> bool:
        """
        Check if the current token has expired.

        Returns:
            bool: True if token is expired, False otherwise.
        """
        token = self.token
        if not token:
            self.__logger.info("No token found in cache, assuming expired.")
            return True

        url = "https://walrus.ninjavan.co/vn/aaa/1.0/external/userscopes"
        session = requests.Session()
        session.headers.update({'Authorization': f'Bearer {token}'})

        try:
            response = session.get(url)
            if response.status_code == 200:
                self.__logger.info("Token is valid.")
                return False
            if response.status_code == 401:
                self.__logger.info("Token has expired.")
                return True
        except requests.RequestException as error:
            self.__logger.error(f"Error checking token expiration: {error}")
            return True
        finally:
            session.close()

    def update_token(self) -> None:
        """
        Update the token by retrieving it from Google Sheets.
        Retry until a valid token is fetched and cached.
        """
        chat_service = GoogleChatService(logger=self.__logger)
        card = self._build_card(
            header='<font color="#de1304">OPv2 Token Expired</font>',
            message=f'Token: "{self.token}".\nPlease update token in Google Sheet.\nRetrying in 60 seconds.'
        )
        chat_service.webhook_send(self.__webhook_url, card=card)
        time.sleep(60)
        try:
            self.__logger.info('Attempting to update token...')
            new_token = self._get_token_from_gsheet()
            if new_token != self.token:
                cache.set(self.TOKEN_CACHE_KEY, new_token, timeout=self.TOKEN_CACHE_TIMEOUT)
                self.__logger.info('Token successfully updated and cached.')

                card = self._build_card(
                    header='<font color="#38761d">OPv2 Token Updated</font>',
                    message=f'Updated token: "{new_token}".'
                )
                chat_service.webhook_send(self.__webhook_url, card=card)
        except Exception as error:
            self.__logger.error(f'Error updating token: {error}')
            raise error

    @staticmethod
    def auto_update_token(func):
        """
        Decorator to automatically update the token if expired before invoking the function.

        Args:
            func (callable): The function to decorate.

        Returns:
            callable: The wrapped function.
        """

        def wrapper(self, *args, **kwargs):
            # Check if the token has expired using the token manager instance
            while self.token_manager.token_is_expired():
                self.token_manager.update_token()  # Access via token_manager
            return func(self, *args, **kwargs)

        return wrapper

    @property
    def token(self) -> str:
        """
        Retrieve the current token from cache.

        Returns:
            str: Cached token or None if not set.
        """
        return cache.get(self.TOKEN_CACHE_KEY)


class BaseService(ABC):
    """
    Base class for API services handling shared logic such as session management and authorization.
    """

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the BaseService with a logger and token manager.
        """
        self._logger = logger
        self.session = requests.Session()
        self.token_manager = TokenManager(logger=self._logger)

    def _set_session_headers(self) -> None:
        """
        Set the session headers for authorization using the current token.
        """
        self.session.headers.update({
            'Authorization': f'Bearer {self.token_manager.token}'
        })

    @staticmethod
    def _process_response(response: requests.Response) -> tuple:
        """
        Process the API response, returning the status code and the content.

        Args:
            response (requests.Response): The response object from the API request.

        Returns:
            tuple: A tuple containing the status code and the response content (JSON or text).
        """
        try:
            return response.status_code, response.json()
        except ValueError:
            return response.status_code, response.text

    @TokenManager.auto_update_token
    def make_request(self, url: str, method: str = 'GET', payload: Any = None, data: Any = None, params: dict = None, files: dict = None) -> tuple:
        """
        Make an API request with retry logic for token expiration.

        Args:
            url (str): The API URL.
            method (str): HTTP method ('GET', 'POST', etc.). Defaults to 'GET'.
            payload (dict, optional): JSON payload for the request.
            data (dict, optional): Form data for the request.
            params (dict, optional): URL parameters for the request.
            files (dict, optional): Files to upload with the request.

        Returns:
            tuple: A tuple containing the status code and the response content.
        """
        self._set_session_headers()

        try:
            self._logger.info(f"Payload: {payload}")
            response = self.session.request(method, url, json=payload, files=files, data=data, params=params)
            self._logger.info(f"{response.url} {response.request.method} {response.status_code}")
            response.raise_for_status()
            return self._process_response(response)

        except requests.exceptions.HTTPError as http_error:
            return self._process_response(http_error.response)

        except requests.exceptions.RequestException as req_error:
            self._logger.error(f"Request exception: {req_error}")
            return 500, {'error': str(req_error)}

        except Exception as general_error:
            self._logger.error(f"An unexpected error occurred: {general_error}")
            return 500, {'error': f'An unexpected error occurred: {general_error}'}
        
        
        
class WMSTokenManager(metaclass=SingletonMeta):
    """
    Duplicate from TokenManager line #20
    """

    TOKEN_CACHE_KEY = "opv2_auth_token"
    TOKEN_CACHE_TIMEOUT = 60 * 60 * 26  # 26 hours

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the TokenManager with a logger and token lock for thread safety.
        """
        self.__logger = logger
        self.__configs = configs
        self.__webhook_url = self.__configs.get('ROOT_NOTIFICATION_WEBHOOK')

    @staticmethod
    def _build_card(header: str, message: str):
        """
        Build a Google Chat notification card for token-related messages.

        Args:
            header (str): Header for the card.
            message (str): Message to be displayed on the card.

        Returns:
            dict: A card representation for Google Chat.
        """
        card_builder = CardBuilder()
        card_header = CardHeader()
        card_header.title = "WMS Token Manager"
        card_header.subtitle = timezone.now().strftime('%d/%m/%Y %H:%M:%S')
        card_builder.set_header(card_header)

        section = Section()
        section.header = header
        section.add_widget(W.TextParagraph(message))
        card_builder.add_section(section)

        return card_builder.card

    def _get_token_from_gsheet(self) -> str:
        """
        Retrieve the token from Google Sheets.

        Returns:
            str: The token retrieved from the Google Sheet.
        """
        try:
            service_account = get_service_account(configs.get('GSA_SYSTEM'))
            gsheets_service = GoogleSheetService(
                service_account=service_account,
                spreadsheet_id=configs.get('CONFIGS_SPREADSHEET_ID'),
                logger=self.__logger
            )
            return gsheets_service.read_cell(
                cell='B2',
                worksheet=configs.get('OPV2_TOKEN_WORKSHEET_ID', cast=int)
            )
        except ServiceAccount.DoesNotExist:
            self.__logger.error('Service Account not found.')
            raise
        except Exception as error:
            self.__logger.error(f'Error reading token from Google Sheet: {error}')
            raise

    def token_is_expired(self) -> bool:
        """
        Check if the current token has expired.

        Returns:
            bool: True if token is expired, False otherwise.
        """
        token = self.token
        if not token:
            self.__logger.info("No token found in cache, assuming expired.")
            return True

        url = "https://walrus.ninjavan.co/vn/aaa/1.0/external/userscopes"
        session = requests.Session()
        session.headers.update({'Authorization': f'Bearer {token}'})

        try:
            response = session.get(url)
            if response.status_code == 200:
                self.__logger.info("Token is valid.")
                return False
            if response.status_code == 401:
                self.__logger.info("Token has expired.")
                return True
        except requests.RequestException as error:
            self.__logger.error(f"Error checking token expiration: {error}")
            return True
        finally:
            session.close()

    def update_token(self) -> None:
        """
        Update the token by retrieving it from Google Sheets.
        Retry until a valid token is fetched and cached.
        """
        chat_service = GoogleChatService(logger=self.__logger)
        card = self._build_card(
            header='<font color="#de1304">WMS Token Expired</font>',
            message=f'Token: "{self.token}".\nPlease update token in Google Sheet.\nRetrying in 60 seconds.'
        )
        chat_service.webhook_send(self.__webhook_url, card=card)
        time.sleep(60)
        try:
            self.__logger.info('Attempting to update token...')
            new_token = self._get_token_from_gsheet()
            if new_token != self.token:
                cache.set(self.TOKEN_CACHE_KEY, new_token, timeout=self.TOKEN_CACHE_TIMEOUT)
                self.__logger.info('Token successfully updated and cached.')

                card = self._build_card(
                    header='<font color="#38761d">WMS Token Updated</font>',
                    message=f'Updated token: "{new_token}".'
                )
                chat_service.webhook_send(self.__webhook_url, card=card)
        except Exception as error:
            self.__logger.error(f'Error updating token: {error}')
            raise error

    @staticmethod
    def auto_update_token(func):
        """
        Decorator to automatically update the token if expired before invoking the function.

        Args:
            func (callable): The function to decorate.

        Returns:
            callable: The wrapped function.
        """

        def wrapper(self, *args, **kwargs):
            # Check if the token has expired using the token manager instance
            while self.token_manager.token_is_expired():
                self.token_manager.update_token()  # Access via token_manager
            return func(self, *args, **kwargs)

        return wrapper

    @property
    def token(self) -> str:
        """
        Retrieve the current token from cache.

        Returns:
            str: Cached token or None if not set.
        """
        return cache.get(self.TOKEN_CACHE_KEY)        
        
        
class WMSBaseService(ABC):
    """
    Base class for API services handling shared logic such as session management and authorization.
    USE ONLY FOR WMS PROCESS ( Only Thinh token can access to WMS )
    """

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the BaseService with a logger and token manager.
        """
        self._logger = logger
        self.session = requests.Session()
        self.token_manager = WMSTokenManager(logger=self._logger)

    def _set_session_headers(self) -> None:
        """
        Set the session headers for authorization using the current token.
        """
        self.session.headers.update({
            'Authorization': f'Bearer {self.token_manager.token}'
        })

    @staticmethod
    def _process_response(response: requests.Response) -> tuple:
        """
        Process the API response, returning the status code and the content.

        Args:
            response (requests.Response): The response object from the API request.

        Returns:
            tuple: A tuple containing the status code and the response content (JSON or text).
        """
        try:
            return response.status_code, response.json()
        except ValueError:
            return response.status_code, response.text

    @WMSTokenManager.auto_update_token
    def make_request(self, url: str, method: str = 'GET', payload: Any = None, data: Any = None, params: dict = None, files: dict = None) -> tuple:
        """
        Make an API request with retry logic for token expiration.

        Args:
            url (str): The API URL.
            method (str): HTTP method ('GET', 'POST', etc.). Defaults to 'GET'.
            payload (dict, optional): JSON payload for the request.
            data (dict, optional): Form data for the request.
            params (dict, optional): URL parameters for the request.
            files (dict, optional): Files to upload with the request.

        Returns:
            tuple: A tuple containing the status code and the response content.
        """
        self._set_session_headers()

        try:
            self._logger.info(f"Payload: {payload}")
            response = self.session.request(method, url, json=payload, files=files, data=data, params=params)
            self._logger.info(f"{response.url} {response.request.method} {response.status_code}")
            response.raise_for_status()
            
            # if response.status_code == 503: 
            #     return 503, {'error': 'Service Unavailable'}
            return self._process_response(response)

        except requests.exceptions.HTTPError as http_error:
            return self._process_response(http_error.response)

        except requests.exceptions.RequestException as req_error:
            self._logger.error(f"Request exception: {req_error}")
            return 500, {'error': str(req_error)}

        except Exception as general_error:
            self._logger.error(f"An unexpected error occurred: {general_error}")
            return 500, {'error': f'An unexpected error occurred: {general_error}'}
