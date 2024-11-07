import logging
from typing import Tuple

from django.utils import timezone

from ..base import BaseService


class ScanService(BaseService):
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

    def parcel_sweeper_live(self, tracking_id: str, hub_id: int = 1, task_id: int = 621340,
                            node_id: int = 621340) -> tuple:
        """
        parcel sweeper live order

        Args:
            tracking_id (str): Tracking ID.
            hub_id (int, optional): Hub ID. Defaults to 1 (VIET).
            task_id (int, optional): Task ID. Defaults to 621340 (VIET).
            node_id (int, optional): Node ID. Defaults to 621340 (VIET).

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """
        url = f'{self._base_url}/sort/2.0/scans/sweeper'
        payload = {
            "hub_id": hub_id,
            "scan": tracking_id,
            "task_id": task_id,
            "node_id": node_id,
            "to_return_dp_id": True,
            "hub_user": None
        }
        return self.make_request(url=url, method='POST', payload=payload)

    def van_inbound(self, route_id: int, tracking_ids: list, waypoint_ids: list) -> tuple:
        parcels = []
        for tracking_id, waypoint_id in zip(tracking_ids, waypoint_ids):
            parcel = {
                "tracking_id": tracking_id,
                "waypoint_id": waypoint_id,
                "inbound_type": "VAN_FROM_NINJAVAN",
                "inbound_date": int(timezone.now().timestamp() * 1000)
            }
            parcels.append(parcel)

        url = f"https://walrus.ninjavan.co/vn/driver/1.0/routes/{route_id}/parcels"
        payload = {
            "parcels": parcels
        }
        return self.make_request(url, method='POST', payload=payload)
