import logging

from stos.utils import paginate_count
from ..base import BaseService
from ..dto import ZoneDTO, HubDTO


class NetworkService(BaseService):
    """
    A class for making API requests to the Order Service.
    """

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the OrderService with a logger and a requests' session.
        """
        super().__init__(logger)
        self._logger = logger
        self._base_url = 'https://api.ninjavan.co/vn'

    def count_zones(self) -> tuple:
        """
        Count zones.

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """
        url = f"{self._base_url}/zones/1.0/zones/props/count"
        return self.make_request(url, method='GET')

    def get_all_zones(self) -> tuple:
        """
        Get all zones.

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """

        # Get total zones
        stt_code, total_zones = self.count_zones()

        if stt_code != 200:
            return stt_code, []

        num_of_zones = total_zones.get('total', 0)
        self._logger.info(f"Total zones: {num_of_zones}")
        pages = paginate_count(num_of_zones, 1000)
        zones = []
        for page, size in pages:
            url = f"{self._base_url}/zones/zones?page_no={page}&size={size}&with_polygon=false"
            stt_code, response = self.make_request(url, method='GET')

            if stt_code != 200:
                logging.error(f"Failed to get zones from the API: {response}")
                continue

            data_list = response.get('zones', [])
            zones.extend([ZoneDTO.from_dict(data) for data in data_list])

        if not zones:
            return 200, []

        return 200, zones

    def get_all_hubs(self, active_only: bool = False) -> tuple:
        url = f"{self._base_url}/sort/2.0/hubs?active_only={str(active_only).lower()}"
        stt_code, response = self.make_request(url, method='GET')

        if stt_code != 200:
            return stt_code, []

        hubs = [HubDTO.from_dict(data) for data in response]

        return 200, hubs
