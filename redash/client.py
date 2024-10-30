import logging
import time
from typing import Optional, Dict, Any, List

import pandas as pd

from .base_api import BaseAPI
from .exceptions import AuthenticationError, FreshError
from .models import StatusChoices, Job


class RedashClient(BaseAPI):
    """
    Client to interact with the Redash API.

    Attributes:
        api_key (str): The API key for authentication.
        __endpoint (str): The endpoint URL for the Redash instance.
        __logger (logging.Logger): Logger instance for logging API interactions.
    """

    def __init__(self, api_key: str, endpoint: Optional[str] = None,
                 logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the RedashClient with the provided API key and endpoint.

        Args:
            api_key (str): The API key for authentication.
            endpoint (Optional[str]): The endpoint URL for the Redash instance.
                                      Defaults to the value in the environment variable REDASH_ENDPOINT.
            logger (logging.Logger): Optional; logger instance for logging.
        """
        if endpoint is None:
            endpoint = 'https://redash-vn.ninjavan.co'

        self.__logger = logger
        self.__endpoint = endpoint
        super().__init__(api_key, self.__endpoint, logger)
        self.test_credentials()

    def test_credentials(self) -> bool:
        """
        Test if the provided credentials are valid.

        Returns:
            bool: True if credentials are valid, False otherwise.
        """
        try:
            response = self.make_request(f"{self.__endpoint}/api/session")
            return response[0] == 200
        except Exception as e:
            self.__logger.error(f"Authentication failed: {e}")
            raise AuthenticationError("Authentication failed.")

    def _poll_job(self, job: Job) -> Job:
        """
        Poll the job status until it is completed, failed, or cancelled.

        Args:
            job (Job): The job to poll.

        Returns:
            Job: The updated job object after polling.
        """
        start_time = time.time()

        while job.status not in (StatusChoices.SUCCESS, StatusChoices.FAILURE, StatusChoices.CANCELLED):
            status_code, response = self.make_request(f"{self.__endpoint}/api/jobs/{job.job_id}")
            self.__logger.info(f"Response [{status_code}] - {response}")

            job_response = response.get('job', {})
            job.status = job_response.get('status', job.status)
            job.error = job_response.get('error') or None
            job.result_id = job_response.get('query_result_id')

            elapsed_time = time.time() - start_time
            sleep_time = min(1 + elapsed_time // 60, 7)
            time.sleep(sleep_time)

        return job

    def fresh_query_result(self, query_id: int, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get a fresh query result by executing the query.

        Args:
            query_id (int): The ID of the query to execute.
            params (Optional[Dict[str, Any]]): Parameters to pass to the query, with string keys.

        Returns:
            List[Dict[str, Any]]: The rows of the query result.

        Raises:
            Exception: If refreshing or fetching results fails.
        """
        params = params or {}
        payload = {'max_age': 0, 'parameters': params}

        status_code, response = self.make_request(
            f"{self.__endpoint}/api/queries/{query_id}/results",
            method='POST',
            payload=payload
        )

        self.__logger.info(f"Response [{status_code}] - {response}")

        if status_code != 200:
            raise Exception('Refresh failed.')

        job, _ = Job.objects.update_or_create(
            job_id=response['job']['id'],
            query_id=query_id
        )

        job = self._poll_job(job)
        job.save()  # Save job status after polling

        if job.status == StatusChoices.SUCCESS:
            result = self.get_result(job.result_id)
            return result

        raise FreshError(f"Job failed with error: {job.error}")

    def get_result(self, result_id: int) -> List[Dict[str, Any]]:
        """
        Get the result of a query by its result ID.

        Args:
            result_id (int): The ID of the query result to fetch.

        Returns:
            List[Dict[str, Any]]: The rows of the query result.

        Raises:
            Exception: If fetching results fails.
        """
        status_code, response = self.make_request(f"{self.__endpoint}/api/query_results/{result_id}.json")

        if status_code != 200:
            raise Exception('Failed getting results.')

        return response['query_result']['data']['rows']

    def get_result_as_df(self, result_id: int) -> pd.DataFrame:
        """
        Get the result of a query by its result ID as a pandas DataFrame.

        Args:
            result_id (int): The ID of the query result to fetch.

        Returns:
            pd.DataFrame: The rows of the query result as a DataFrame.

        Raises:
            Exception: If fetching results fails.
        """
        rows = self.get_result(result_id)

        try:
            df = pd.DataFrame(rows)
        except Exception as e:
            self.__logger.error(f"Error converting rows to DataFrame: {e}")
            raise Exception("Error converting rows to DataFrame.")

        return df
