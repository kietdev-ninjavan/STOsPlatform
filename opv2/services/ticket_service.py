import io
import logging
from typing import List, Tuple, Optional

import pandas as pd

from stos.utils import chunk_list
from ..base import BaseService
from ..base.ticket import TicketStatusChoices, TicketTypeChoices, TicketSubTypeChoices
from ..dto import TicketResolveDTO, TicketDTO, CancelTicketDTO, TicketCreateDTO

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

    def cancel_tickets(self, cancel_dtos: List[CancelTicketDTO]) -> Tuple[int, dict]:
        url = f"{self._base_url}/ticketing/tickets/massupdate"
        self._logger.info(f'Have {len(cancel_dtos)} tickets to resolve')

        # Return if there are no tickets to resolve
        if not cancel_dtos:
            return 200, {'success': [], 'failed': []}

        success, failed = [], []
        # Chunk the payload to avoid hitting the API limit
        for chunk in chunk_list(cancel_dtos, 1000):
            payload = [cancel_dto.to_dict() for cancel_dto in chunk]
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
            return 400, {'error': 'Failed to cancel tickets'}

        return 200, {'success': success, 'failed': failed}

    def get_ticket_by_tracking_ids(self, tracking_ids: list, ticket_types: Optional[List[TicketTypeChoices]] = None,
                                   ticket_sub_types: Optional[List[TicketSubTypeChoices]] = None) -> Tuple[int, List[TicketDTO]]:
        tickets = []
        if not tracking_ids:
            return 200, tickets

        ticket_types = [ticket_type.value for ticket_type in ticket_types] if ticket_types else []
        ticket_sub_types = [ticket_sub_type.value for ticket_sub_type in ticket_sub_types] if ticket_sub_types else []

        for chunk in chunk_list(tracking_ids, 1000):
            url = f'{self._base_url}/ticketing/2.0/tickets/search?page=1&page_size=1000'
            payload = {
                'entry_sources': [],
                'investigating_parties': [],
                'ticket_statuses': [
                    TicketStatusChoices.IN_PROGRESS.value,
                    TicketStatusChoices.PENDING.value,
                ],
                'ticket_types': ticket_types,
                'ticket_sub_types': ticket_sub_types,
                'tracking_ids': chunk,
                'investigating_hub_ids': []
            }
            stt_code, result = self.make_request(url, method="POST", payload=payload)

            if stt_code != 200:
                self._logger.error(f"Failed to get tickets by tracking ids: {chunk} as {result}")
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

    def get_detail_tickets(self, ticket_ids: List[int]) -> Tuple[int, dict]:
        if not ticket_ids:
            return 200, {}
        results = {}
        for ticket_id in ticket_ids:
            url = f'{self._base_url}/ticketing/tickets/{ticket_id}'
            stt_code, result = self.make_request(url, method="GET")

            if stt_code != 200:
                self._logger.error(f"Failed to get ticket detail: {ticket_id}")
                continue

            results[f'{ticket_id}'] = result

        return 200, results

    def create_tickets(self, data: List[TicketCreateDTO]) -> tuple:
        """
        Creates multiple tickets by sending a bulk create request.

        Args:
            data (List[TicketDTO]): A list of TicketDTO instances.

        Returns:
            Tuple[int, Dict[str, Union[str, List[int]]]]: A status code and a dictionary containing the results.
        """
        url = f"{self._base_url}/ticketing/2.0/tickets/bulk-create"

        # Convert data to a DataFrame and save as in-memory CSV
        columns = [
            'tracking_id',
            'type',
            'sub_type',
            'investigating_group',
            'assignee_email',
            'investigating_hub_id',
            'entry_source',
            'ticket_notes'
        ]
        df = pd.DataFrame([ticket.to_dict() for ticket in data], columns=columns)

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)  # Move cursor to the beginning of the stream

        # Send the bulk create request
        status_code, response = self.make_request(
            url,
            method='POST',
            files={'file': ('tickets.csv', csv_buffer, 'text/csv')}
        )

        if status_code != 200:
            self._logger.warning(f"Failed to create tickets: {response}")
            return 400, {"error": "Failed to create tickets"}

        # Process the response to determine success and failure
        success, failed = {}, []
        for ticket in response:
            if ticket.get('status') == 'Success':
                success[ticket.get('trackingId')] = ticket.get('ticket')
            else:
                failed.append(ticket.get('trackingId'))

        return 200, {"success": success, "failed": failed}
