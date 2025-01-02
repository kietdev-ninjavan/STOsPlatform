import logging
from typing import Optional,List
from .base_api import BaseAPI
from .exceptions import AuthenticationError

logger = logging.getLogger(__name__)

class MetabaseClient(BaseAPI):
    """
    Client to interact with the Metabase API.

    Attributes:
        session_id (str): The Session for authentication.
        __endpoint (str): The endpoint URL for the Metabase instance.
        __logger (logging.Logger): Logger instance for logging API interactions.
    """
    
    def __init__(self, session_id: str, endpoint: Optional[str] = None,
                 logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the MetabaseClient with the provided API key and endpoint.

        Args:
            session_id (str): The Session for authentication.
            endpoint (Optional[str]): The endpoint URL for the Redash instance.
                                      Defaults to the value in the environment variable METABASE_ENDPOINT.
            logger (logging.Logger): Optional; logger instance for logging.
        """
        if not session_id:
            logger.error("Metabase Session ID is missing.")
            raise ValueError("Metabase Session ID is missing.")

        if endpoint is None:
            endpoint = 'https://metabase.ninjavan.co'

        self.__logger = logger
        self.__endpoint = endpoint
        super().__init__(session_id, self.__endpoint, logger)
        self.test_credentials()
        
    def test_credentials(self) -> bool:
        """
        Test if the provided credentials are valid.

        Returns:
            bool: True if credentials are valid, False otherwise.
        """
        try:
            response = self.make_request(f"{self.__endpoint}/api/user/current")
            return response[0] == 200
        except Exception as e:
            self.__logger.error(f"Authentication failed: {e}")
            raise AuthenticationError("Authentication failed.")
        
    def get_question_properties(self, question_id: int) -> dict:
        """
            Get properties of a question
        Args:
            question_id (int): question id to retrieve properties

        Returns:
            dict: Dictionary of question paramters
        """
        url = f"{self.__endpoint}/api/card/{question_id}"
        
        code, response = self.make_request(url, method= "GET")
        
        if code != 200: 
            logger.error(f"Fail to get question properties: {response}") 
            return {}
        
    
        dataset_query = response.get("dataset_query")
        parameters = dataset_query.get("native").get("template-tags")
        print(parameters)
        params = [ value for key,value in parameters.items() if value["type"] != "snippet" ]
        info = {
            "question_name" : response.get("name"),
            "last_query_start" : response.get("last_query_start"),
            "updated_at" : response.get("updated_at"),
            "last_edit_info" : response.get("last-edit-info"),
            "question_params" : params
        }
        
        return info
        
    def execute_question(self, question_id: int,
                         parameters: List[dict] = []) -> List[dict]:
        """
        Execute a metabase question by id

        Args:
            question_id (int): question id to execute
            parameters (List[dict], optional): List of question's parameters. Defaults to [].

        Returns:
            List[dict]: List of question's result
        """
        url = f"{self.__endpoint}/api/card/{question_id}/query"
        payload = {
            "collection_preview" : False,
            "ignore_cache" : True,
            "parameters" : parameters
        }
        code , response = self.make_request(url, method="POST", payload=payload)
        
        if code != 202:
            logger.error(f"Fail to execute question: {response}")
            return {}
        
        data = response.get("data")
        columns = [ value["display_name"] for value in data.get("cols")]
        rows = data.get("rows")
        result = [
            {
                columns[i]: row[i]
                for i in range(len(columns))
            }
            for row in rows
            
        ]        
        return result