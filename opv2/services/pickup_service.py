import logging
from typing import List

from stos.utils import chunk_list
from ..base import BaseService
from ..base.pickup import BasePickup


class PickupService(BaseService):
    """
    A class for making API requests to the Order Service.
    """

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the OrderService with a logger and a requests' session.
        """
        super().__init__(logger)
        self._logger = logger
        self._base_url = 'https://walrus.ninjavan.co/vn'

    def get_info(self, pickup_jobs: List[BasePickup]) -> tuple:
        url = f"{self._base_url}/pa-job-search/search"
        chunks = chunk_list(pickup_jobs, 500)
        data = []
        for chunk in chunks:
            payload = {
                "limit": 500,
                "use_pit_pagination": False,
                "query": {
                    "pickup_appointment_job_id": {
                        "in": [pickup.job_id for pickup in chunk]
                    }
                }
            }
            status_code, result = self.make_request(url, method='POST', payload=payload)
            if status_code == 200 and "data" in result:
                data.extend(result["data"])

        if not data:
            return 404, {"message": "No data found"}

        return 200, {'data': data}

    def add_route(self, pickup_job_id: int, route_id: int) -> tuple:
        url = f"{self._base_url}/core/pickup-appointment-jobs/{pickup_job_id}/route"
        payload = {
            "new_route_id": route_id,
            "overwrite": True
        }
        return self.make_request(url, method='PUT', payload=payload)
