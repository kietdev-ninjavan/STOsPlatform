import logging

from ..base import BaseService


class RouteService(BaseService):
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the UploadService with a logger and a requests' session.
        """
        super().__init__(logger)
        self.__base_url = 'https://walrus.ninjavan.co/vn'

    def fetch_route(self) -> tuple:
        url = f"{self.__base_url}/driver/3.0/routes"
        payload = ""
        return self.make_request(url, method='GET', data=payload)
