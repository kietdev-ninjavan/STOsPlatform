import logging
from datetime import datetime
from typing import List, Tuple, Union, Dict
import time
import fireducks.pandas as pd
from django.utils import timezone
from pandas.core.interchange.dataframe_protocol import DataFrame

from stos.utils import chunk_list
from ..base import BaseService
from ..base.order import BaseOrder, TagChoices
from ..dto import OrderDTO, AllOrderSearchFilterDTO, AddressDTO, BulkAVDTO


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
            try:
                order_data = item.get("order")
                if order_data:
                    order_dto = OrderDTO.from_dict(order_data)
                    orders[order_dto.tracking_id] = order_dto
            except Exception as e:
                logging.error(f"Failed to convert search data to OrderDTO: {e}")

        return orders

    def create_batch(self) -> tuple:
        """
        Create a batch.

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """
        url = f"{self._base_url}/order-create/internal/4.1/batch"
        return self.make_request(url, method='POST')

    def search_all(self, data: List[Union[str, int]], filter_by_shipper: bool = False,
                   search_filters: List[AllOrderSearchFilterDTO] = None,
                   start_date: datetime = None, end_date: datetime = None,
                   time_range_type: str = "created_at") -> Tuple[int, Dict[str, OrderDTO]]:
        """
        Searches for orders based on the provided data.

        Args:
            data (List[Union[str, int]]): List of tracking IDs or global shipper IDs.
            filter_by_shipper (bool, optional): Whether to filter by shipper. Defaults to False.
            search_filters (List[AllOrderSearchFilterDTO], optional): List of search filters. Defaults to None.
            start_date (datetime, optional): The start date for the search range. Defaults to None.
            end_date (datetime, optional): The end date for the search range. Defaults to None.

        Returns:
            Tuple[int, dict]: A tuple containing the status code and the search result.
        """
        # Split the data into chunks of 1000 items
        chunks = chunk_list(data, 1000)
        search_data = {}
        # Precompute search filters if they exist to avoid adding them repeatedly
        filter_dicts = [search_filter.to_dict() for search_filter in search_filters] if search_filters else []

        # Construct the search range if both dates are provided
        search_range = None
        if start_date and end_date:
            search_range = {
                "field": time_range_type,
                "start_time": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "end_time": end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            }

        # Iterate over chunks and make requests
        for chunk in chunks:
            # Construct the URL for each chunk
            url = f'{self._base_url}/order-search/search'
            total = 1000
            # Construct the payload with the search filters and range
            payload = {
                "search_filters": [
                    {
                        "field": "global_shipper_id" if filter_by_shipper else "tracking_id",
                        "values": chunk
                    },
                    *filter_dicts  # Include additional filters if provided
                ],
                "search_range": search_range,
                "search_field": None
            }

            params = {
                "size": 1000,
                'search_after': None
            }

            while total > 0:
                # Make the request to the API
                status_code, result = self.make_request(url, method='POST', payload=payload, params=params)
                print(status_code)
                if status_code != 200:
                    self._logger.error(f"Failed to search for orders: {result}")
                    continue
                # Check the response status and process the result if successful
                if status_code == 200 and "search_data" in result:
                    orders = self.__convert_search_data_to_order_dto(result["search_data"])
                    search_data.update(orders)

                if result['total'] > total:
                    params['search_after'] = result['search_data'][-1].get('order').get('id')

                total = result['total'] - len(search_data)

        # Return the appropriate response based on whether any data was found
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

    def add_tags(self, order_ids: List[int], tags: List[TagChoices]) -> Tuple[int, dict]:
        """
        Add tags to orders.

        Args:
            order_ids (List[int]): List of order IDs.
            tags (List[TagChoices]): List of tags to add.

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """

        if not order_ids or not tags:
            return 200, {'success': [], 'failed': []}

        url = f'{self._base_url}/core/orders/tags/append-bulk'
        payload = [
            {
                "order_id": order_id,
                "tags": [tag.value for tag in tags]
            } for order_id in order_ids
        ]
        success, failed = [], []
        for chunk in chunk_list(payload, 100):
            stt_code, result = self.make_request(url, method='POST', payload=chunk)

            if stt_code != 200:
                self._logger.error(f"Failed to add tags: {result}")
                failed.extend([order['order_id'] for order in chunk])
                continue

            success.extend(result['data'].get('successful_order_ids', []))
            failed.extend(result['data'].get("failed_orders", []))

        return 200, {'success': success, 'failed': failed}

    def remove_tags(self, order_ids: List[int], tags: List[TagChoices]) -> Tuple[int, dict]:
        """
        Remove tags from orders.

        Args:
            order_ids (List[int]): List of order IDs.
            tags (List[TagChoices]): List of tags to remove.

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """

        if not order_ids or not tags:
            return 200, {'success': [], 'failed': []}

        success, failed = [], []
        for order_id in order_ids:
            url = f'{self._base_url}/core/orders/{order_id}/tags'
            payload = {
                "order_id": order_id,
                "tags": [tag.value for tag in tags]
            }

            status_code, result = self.make_request(url, method='DELETE', payload=payload)

            if status_code != 200:
                self._logger.error(f"Failed to remove tags order {order_id}: {result}")
                failed.append(order_id)

            success.append(order_id)

        return 200, {'success': success, 'failed': failed}

    def parcel_address_search(self, shipper_ids: List[int], df: bool = False) -> Tuple[
        int, Union[List[AddressDTO], DataFrame]]:
        url = f"{self._base_url}/av/parceladdress/search/paginated"
        payload = {
            'from': 0,
            'size': 10000,
            'search_criteria': {
                'created_at': {
                    'to': (timezone.now() - timezone.timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S+0700'),
                    'from': (timezone.now() - timezone.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%S+0700')
                },
                'av_statuses': [
                    'VERIFIED'
                ],
                'rts': False,
                # Turn this on when run officially
                "global_shipper_ids": shipper_ids,
                'av_sources': [
                    'Bulk AV',
                    'Auto AV'
                ]
            }
        }
        stt_code, data = self.make_request(url, method='POST', payload=payload)

        if stt_code != 200:
            return stt_code, []

        result = [
            AddressDTO.form_dict(item) for item in data.get('data', [])
        ]

        if df:
            return stt_code, pd.DataFrame([vars(address) for address in result])

        return stt_code, result

    def bulk_update_av(self, data: List[BulkAVDTO]) -> Tuple[int, dict]:
        url = f"{self._base_url}/av/1.0/verify-address/bulk/update"
        payload = {"waypoints": [item.to_dict() for item in data]}

        stt_code, result = self.make_request(url, method='POST', payload=payload)

        if stt_code != 200:
            return stt_code, result

        success_ids = [wp['id'] for wp in result['waypoints'] if wp['status']]
        failed_ids = [wp['id'] for wp in result['waypoints'] if not wp['status']]

        return stt_code, {"success": success_ids, "failed": failed_ids}

    def get_events(self, order_id: int) -> Tuple[int, dict]:
        url = f"{self._base_url}/events/1.0/orders/{order_id}/events?masked=false"
        stt_code, data = self.make_request(url, method='GET')

        if stt_code != 200:
            return stt_code, data

        return stt_code, data.get('data', [])
