import requests


class BaseAPI:
    """
    A base class for making API requests.

    Attributes:
        api_key (str): The API key for authorization.
        endpoint (str): The API endpoint.
        session (requests.Session): A session object for making requests.
    """

    def __init__(self, api_key: str, endpoint: str, logger):
        """
        Initializes the BaseAPI class with the given API key and endpoint.

        Args:
            api_key (str): The API key for authorization.
            endpoint (str): The API endpoint.
        """
        self.__logger = logger
        self.api_key = api_key
        self.__endpoint = endpoint
        self.session = requests.Session()

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

    def _set_session_headers(self):
        """Sets the authorization header for the session."""
        self.session.headers.update({
            'Authorization': f'Key {self.api_key}'
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
