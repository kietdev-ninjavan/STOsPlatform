
import logging
import time
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
from .base_api import BaseAPI
from .exceptions import AuthenticationError, FreshError

logger = logging.getLogger(__name__)

class MetabaseClient(BaseAPI):
    
    
    
    def __init__(self, session_id: str, endpoint: Optional[str] = None,
                 logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the MetabaseClient with the provided API key and endpoint.

        Args:
            session_id (str): The Session for authentication.
            endpoint (Optional[str]): The endpoint URL for the Redash instance.
                                      Defaults to the value in the environment variable REDASH_ENDPOINT.
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
        
        url = f"{self.__endpoint}/api/card/{question_id}"
        
        code, response = self.make_request(url, method= "GET")
        
        if code != 200: 
            logger.error(f"Fail to get question properties: {response}") 
            return {}
        
    
        dataset_query = response.get("dataset_query")
        parameters = dataset_query.get("native").get("template-tags")
        params = [ value for key,value in parameters if value["type"] != "snippet" ]
        info = {
            "question_name" : response.get("name"),
            "last_query_start" : response.get("last_query_start"),
            "updated_at" : response.get("updated_at"),
            "last_edit_info" : response.get("last-edit-info"),
            "question_params" : params
        }
        
        return info
        
    def execute_question(self, question_id: int,
                         parameters: dict) -> dict:
        
        url = f"{self.__endpoint}/api/card/{question_id}"