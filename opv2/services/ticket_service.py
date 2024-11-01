import logging
from typing import List

from stos.utils import chunk_list
from ..base import BaseService
from ..base.ticket import TicketStatusChoices
from ..dto import TicketResolveDTO, TicketDTO

logger = logging.getLogger(__name__)


class TicketService(BaseService):
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the OrderService with a logger and a requests' session.
        """
        super().__init__(logger)
        self._logger = logger
        self._base_url = 'https://walrus.ninjavan.co/vn'

    def resolve_tickets(self, resolve_dtos: List[TicketResolveDTO]) -> tuple:
        url = f'{self._base_url}/ticketing/tickets/massupdate'
        self._logger.info(f'Have {len(resolve_dtos)} tickets to resolve')

        # Return if there are no tickets to resolve
        if not resolve_dtos:
            return 200, {'success': [], 'failed': []}

        success, failed = [], []
        # Chunk the payload to avoid hitting the API limit
        for chunk in chunk_list(resolve_dtos, 1000):
            payload = [resolve_dto.to_dict() for resolve_dto in chunk]
            stt_code, result = self.make_request(url, method="PUT", payload=payload)

            if stt_code != 200:
                self._logger.error(f"Failed to resolve tickets: {result}")
                failed.extend([resolve_dto.ticket_id for resolve_dto in chunk])
                continue

            for ticket_id, detail in result.get('tickets').items():
                if detail.get('status').lower() == 'success':
                    success.append(ticket_id)
                else:
                    failed.append(ticket_id)

        self._logger.info(
            f"Resolved tickets successfully - success: {len(success)}, failed: {len(failed)}"
        )

        if not success:
            return 400, {'error': 'Failed to resolve tickets'}

        return 200, {'success': success, 'failed': failed}

    def get_ticket_by_tracking_ids(self, tracking_ids: list) -> tuple:
        tickets = []
        for chunk in chunk_list(tracking_ids, 1000):
            url = f'{self._base_url}/ticketing/2.0/tickets/search?page=1&page_size=1000'
            payload = {
                'entry_sources': [],
                'investigating_parties': [],
                'ticket_statuses': [
                    TicketStatusChoices.IN_PROGRESS.value,
                    TicketStatusChoices.PENDING.value,
                ],
                'ticket_types': [],
                'tracking_ids': chunk,
                'investigating_hub_ids': []
            }
            stt_code, result = self.make_request(url, method="POST", payload=payload)

            if stt_code != 200:
                self._logger.error(f"Failed to get tickets by tracking ids: {chunk}")
                continue

            data = result.get('data')
            if not data:
                continue

            try:
                tickets.extend([TicketDTO.from_dict(ticket) for ticket in data])
            except Exception as e:
                self._logger.error(f"Error parsing tickets: {e}")
                continue
        self._logger.info(f"Loaded {len(tickets)}/{len(tracking_ids)} tickets.")
        return 200, tickets
