import logging
from datetime import datetime
from typing import List, Tuple, Union, Dict

from django.utils import timezone

from stos.utils import chunk_list
from ..base import BaseService
from ..base.order import BaseOrder
from ..dto import OrderDTO


class OrderService(BaseService):
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

    @staticmethod
    def __convert_search_data_to_order_dto(search_data: List[dict]) -> Dict[str, OrderDTO]:
        orders = {}
        for item in search_data:
            order_data = item.get("order")
            if order_data:
                order_dto = OrderDTO.from_dict(order_data)
                orders[order_dto.tracking_id] = order_dto
        return orders

    def create_batch(self) -> tuple:
        """
        Create a batch.

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """
        url = f"{self._base_url}/order-create/internal/4.1/batch"
        return self.make_request(url, method='POST')

    def search_all(self, data: List[Union[str, int]], filter_by_shipper: bool = False, start_date: datetime = None,
                   end_date: datetime = None) -> Tuple[int, Dict[str, OrderDTO]]:
        """
        Searches for orders based on the provided data.

        Args:
            data (List[Union[str, int]]): List of tracking IDs or global shipper IDs.
            filter_by_shipper (bool, optional): Whether to filter by shipper. Defaults to False.
            start_date (datetime, optional): The start date for the search range. Defaults to None.
            end_date (datetime, optional): The end date for the search range. Defaults to None.

        Returns:
            Tuple[int, dict]: A tuple containing the status code and the search result.
        """
        chunks = chunk_list(data, 1000)
        search_data = {}

        for chunk in chunks:
            url = f'{self._base_url}/order-search/search?size={len(chunk)}'
            payload = {
                "search_filters": [
                    {
                        "field": "global_shipper_id" if filter_by_shipper else "tracking_id",
                        "values": chunk
                    },
                ],
                "search_range": (
                    {
                        "field": "created_at",
                        "start_time": start_date.strftime('%Y-%m-%dT00:00:00Z'),
                        "end_time": end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
                    } if start_date and end_date else None
                ),
                "search_field": None
            }

            status_code, result = self.make_request(url, method='POST', payload=payload)
            if status_code == 200 and "search_data" in result:
                orders = self.__convert_search_data_to_order_dto(result["search_data"])
                search_data.update(orders)

        if not search_data:
            return 404, {}

        return 200, search_data

    def change_to_address(self, order_id: int, address1: str, address2: str, city: str, ) -> tuple:
        url = f"{self._base_url}/core/2.0/orders/{order_id}"
        payload = {
            "to": {
                "address": {
                    "address1": address1,
                    "address2": address2,
                    "city": city,
                    "country": "VN",
                    "postcode": ""
                }
            }
        }
        return self.make_request(url, method='PATCH', payload=payload)

    def reschedule(self, orders: List[BaseOrder], date: datetime = None) -> Tuple[int, dict]:
        """
        Reschedule orders.

        Args:
            orders (List[OrderDTO]): List of orders to reschedule.
            date (datetime, optional): The date to reschedule the orders to. Defaults to None.

        Returns:
            Tuple[int, int]: A tuple containing status code and the number of successfully rescheduled orders.
        """
        if not orders:
            return 200, {}

        success, fail = [], []
        url = f"{self._base_url}/core/orders/reschedule-bulk"
        for chunk in chunk_list(orders, 100):
            payload = [
                {
                    "order_id": order.order_id,
                    "tracking_id": order.tracking_id,
                    "date": date.strftime('%Y-%m-%d') if date else timezone.now().strftime('%Y-%m-%d')
                } for order in chunk
            ]

            status_code, result = self.make_request(url, method='POST', payload=payload)

            if status_code != 200:
                fail.extend([order.order_id for order in chunk])
                self._logger.error(f"Failed to reschedule orders: {fail}")
                continue

            success.extend(result['data'].get('successful_order_ids', []))
            fail.extend([order['order_id'] for order in result['data'].get('failed_orders', [])])

        return 200, {"successful_orders": success, "failed_orders": fail}

    def pull_route(self, order_id: int) -> tuple:
        """
        Pull route information for an order.

        Args:
            order_id (int): The order ID.

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """
        url = f'{self._base_url}/core/2.0/orders/{order_id}/routes'
        payload = {
            "type": "DELIVERY"
        }
        return self.make_request(url, method='DELETE', payload=payload)
