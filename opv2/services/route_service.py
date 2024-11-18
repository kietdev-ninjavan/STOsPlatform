import logging
from datetime import datetime

from django.utils import timezone

from ..base import BaseService


class RouteService(BaseService):
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

    def create_route(self, driver_id: int = None, delivery_date: datetime = None, hub_id: int = 1,
                     zone_id: int = 2) -> tuple:
        """
        Create a route in the system

        Args:
            driver_id (int): driver id
            delivery_date (datetime): delivery date
            hub_id (int): default hub id 1 for VIET
            zone_id (int): default zone id 2 for All Zone

        Returns:
            Tuple[int, int]: A tuple containing status code and response data
            success: 201
        """
        delivery_date = timezone.now() if not delivery_date
        delivery_date_str = delivery_date.strftime("%Y-%m-%d")
        delivery_datetime = delivery_date - timezone.timedelta(hours=7)
        delivery_datetime_str = delivery_datetime.strftime("%Y-%m-%dT00:00:00Z")
        url = f'{self._base_url}/route-v2/routes'
        payload = {
            "date": delivery_date_str,
            "datetime": delivery_datetime_str,
            "driver_id": driver_id,
            "hub_id": hub_id,
            "zone_id": zone_id
        }
        stt_code, result = self.make_request(url=url, method='POST', payload=payload)

        if stt_code != 201:
            return stt_code, result

        route_id = result['data'].get('id')

        return stt_code, route_id

    def assign_driver(self, driver_id: int, route_id: int, delivery_date: datetime = None, hub_id: int = 1, zone_id: int = 2):
        """
        Add a driver to a route

        :param delivery_date:
        :param driver_id: driver id
        :param route_id: route id
        :param hub_id: hub id (default 1 for VIET)
        :param zone_id: zone id (default 2 for All Zone)
        :return: Status code (int) and result (dict)
        success: 204
        """

        payload = {
            "date": delivery_date.strftime("%Y-%m-%d") if delivery_date else timezone.now().strftime("%Y-%m-%d"),
            "driver_id": driver_id,
            "hub_id": hub_id,
            "zone_id": zone_id
        }

        url = f"{self._base_url}/route-v2/routes/{route_id}/details"
        return self.make_request(url, method='PUT', payload=payload)

    def start_route(self, route_id: int, driver_id: int, tracking_ids: list) -> tuple:
        """
        Start a route

        Args:
            route_id (int): route id
            driver_id (int): driver id
            tracking_ids (list): list of tracking ids
        Returns:
            Tuple[int, dict]: A tuple containing status code and response data
        """

        parcels = [
            {
                "tracking_id": tracking_id,
                "scanned_at": timezone.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            } for tracking_id in tracking_ids
        ]

        self.session.headers.update({'X-Nv-Page-Url': 'stos-start-route'})
        url = f"{self._base_url}/driver/2.0/routes/{route_id}/start"
        payload = {
            "driver_id": driver_id,
            "parcels": parcels
        }

        return self.make_request(url, payload=payload, method='POST')

    def archive_route(self, route_id: int):
        """
        Archive a route

        :param route_id: route id
        :return: Status code (int) and result (dict)
        success: 204
        """
        url = f"{self._base_url}/route-v2/routes/{route_id}/archive"
        return self.make_request(url, method='PUT')

    def get_manifest(self, route_id: int):
        """
        Get manifest for a route

        :param route_id: route id
        :return: Status code (int) and result (dict)
        """
        url = f"https://walrus.ninjavan.co/vn/route-v2/routes/{route_id}/waypoints?masked=false&sortBySeqNo=true"
        return self.make_request(url, method='GET')

    def add_order_to_route(self, order_id: int, route_id: int) -> tuple:
        """
        Add an order to a route

        Args:
            order_id (str): order id
            route_id (int): route id

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data
            success: 204
        """

        url = f'{self._base_url}/route-v2/routes/{route_id}/orders/{order_id}?route_source=ADD_BY_ORDER&transaction_type=DELIVERY'
        payload = {
            "route_id": route_id,
            "type": "DELIVERY"
        }
        return self.make_request(url, payload=payload, method='PUT')
