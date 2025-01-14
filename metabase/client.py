import logging
from typing import Optional, List

from .base_api import BaseAPI

logger = logging.getLogger(__name__)


class MetabaseClient(BaseAPI):
    """
    Client to interact with the Metabase API.

    Attributes:
        __endpoint (str): The endpoint URL for the Metabase instance.
        __logger (logging.Logger): Logger instance for logging API interactions.
    """

    def __init__(self, endpoint: Optional[str] = None,
                 logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the MetabaseClient with the provided API key and endpoint.

        Args:
            endpoint (Optional[str]): The endpoint URL for the Metabase instance.
                                      Defaults to the value in the environment variable METABASE_ENDPOINT.
            logger (logging.Logger): Optional; logger instance for logging.
        """

        if endpoint is None:
            endpoint = 'https://metabase.ninjavan.co'

        super().__init__(endpoint=endpoint, logger=logger)
        self.__logger = logger
        self.__endpoint = endpoint

    def get_question_properties(self, question_id: int) -> dict:
        """
            Get properties of a question
        Args:
            question_id (int): question id to retrieve properties

        Returns:
            dict: Dictionary of question paramters
        """
        url = f"{self.__endpoint}/api/card/{question_id}"

        code, response = self.make_request(url, method="GET")

        if code != 200:
            self.__logger.error(f"Fail to get question properties: {response}")
            return {}

        dataset_query = response.get("dataset_query")
        parameters = dataset_query.get("native").get("template-tags")
        params = [
            value
            for key, value in parameters.items()
            if value["type"] != "snippet"
        ]
        self.__logger.info(f"Collected {len(params)} parameters from question {question_id}")

        info = {
            "question_name": response.get("name"),
            "last_query_start": response.get("last_query_start"),
            "updated_at": response.get("updated_at"),
            "last_edit_info": response.get("last-edit-info"),
            "question_params": params
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
            "collection_preview": False,
            "ignore_cache": True,
            "parameters": parameters
        }
        code, response = self.make_request(url, method="POST", payload=payload)

        if code != 202:
            logger.error(f"Fail to execute question: {response}")
            return {}

        data = response.get("data")
        columns = [value["display_name"] for value in data.get("cols")]
        rows = data.get("rows")
        if not rows:
            self.__logger.error("No data returned for this execution")
            return []

        result = [
            {
                columns[i]: row[i]
                for i in range(len(columns))
            }
            for row in rows
        ]

        self.__logger.info(f"Collected {len(result)} rows from question {question_id}")
        return result
