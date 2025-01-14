import logging
from typing import List, Tuple, Union

from ..base import BaseService
from ..dto import ShipperDTO


class ShipperService(BaseService):
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the OrderService with a logger and a requests' session.
        """
        super().__init__(logger)
        self._logger = logger
        self._base_url = 'https://walrus.ninjavan.co/vn'

    def shipper_search(self, value: Union[str, int]) -> Tuple[int, List[ShipperDTO]]:
        """
        Search for all shippers with keyword.

        Args:
            value (Union[str, int]): Search value.

        Returns:
            Tuple[int, List[ShipperDTO]]: A tuple containing status code and response data.
        """
        url = f'{self._base_url}/shipper-search/shippers/list'
        PAGE_SIZE = 500  # Maximum number of items per page (OPv2 Support)

        # Prepare payload
        payload = {
            "from": 0,
            "size": 500,
            "system_id": ["vn"],
            "name": value
        }

        shippers = []

        try:
            while True:
                # Make the request
                status_code, response = self.make_request(url, method='POST', payload=payload)

                # Handle HTTP errors
                if status_code != 200:
                    return status_code, []

                # Extract results and update shippers
                shipper_list = [ShipperDTO.from_dict(shipper) for shipper in response.get('details', [])]
                returned_size = response.get('returned_size', 0)
                shippers.extend(shipper_list)

                # Break loop if no more data
                if returned_size < PAGE_SIZE:
                    break

                # Move to the next page
                payload['from'] += PAGE_SIZE

            return 200, shippers

        except Exception as e:
            # Handle unexpected errors
            self._logger.exception(f"Error occurred: {str(e)}")
            return 500, []
