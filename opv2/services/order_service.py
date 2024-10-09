import logging

from ..base import BaseService


class OrderService(BaseService):
    """
    A class for making API requests to the Order Service.
    """

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the OrderService with a logger and a requests' session.
        """
        super().__init__(logger)
        self.base_url = 'https://walrus.ninjavan.co/vn'

    def create_batch(self) -> tuple:
        """
        Create a batch.

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """
        url = f"{self.base_url}/order-create/internal/4.1/batch"
        return self.make_request(url, method='POST')
