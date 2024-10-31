import logging

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from ..base.service import TokenManager

logger = logging.getLogger(__name__)


class GraphQLService:
    """
    A GraphQL client with token management and retry logic.
    """

    def __init__(self, url: str, logger: logging.Logger = logger):
        """
        Initialize the GraphQLClientWithToken with a logger, token manager, and client transport.
        """
        self.logger = logger
        self.token_manager = TokenManager(logger)
        self.url = url
        self.transport = self._create_transport()

    def _create_transport(self):
        """
        Create a new transport for the GraphQL client using the current token.
        """
        return RequestsHTTPTransport(
            url=self.url,
            headers={"Authorization": f"Bearer {self.token_manager.token}"},
            use_json=True,
        )

    def _refresh_transport(self):
        """
        Refresh the transport after updating the token.
        """
        self.transport = self._create_transport()

    @TokenManager.auto_update_token
    def execute_query(self, query: gql, variables: dict):
        """
        Execute the GraphQL query with retry logic for token expiration.
        """
        self._refresh_transport()
        client = Client(transport=self.transport, fetch_schema_from_transport=True)

        try:
            return client.execute(query, variable_values=variables)
        except Exception as e:
            raise e
