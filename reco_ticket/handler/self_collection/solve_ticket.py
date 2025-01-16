import logging

from django.db.models import Q
from django.utils import timezone

from opv2.dto import TicketResolveDTO
from opv2.services import TicketService
from ...models import TicketSelfCollection, SelfCollectionChoices

logger = logging.getLogger(__name__)


def solve_sc_tt_destroyed_goods():
    # Get tickets
    data = TicketSelfCollection.objects.filter(
        Q(type=SelfCollectionChoices.TT_DESTROYED_GOODS)
        & Q(resolve_at__isnull=True)
    )

    # make DTO
    resolve_dtos = [
        TicketResolveDTO(
            tracking_id=ticket.tracking_id,
            ticket_id=ticket.ticket_id,
            custom_fields=[],
            order_outcome='PARCEL SCRAPPED',
            new_instruction='', )
        for ticket in data
    ]

    ticket_svc = TicketService(logger)
    stt_code, tickets = ticket_svc.resolve_tickets(resolve_dtos)

    if stt_code != 200:
        raise Exception(f"Error when resolve tickets: {tickets}")

    # Update ticket
    data.update(resolve_at=timezone.now())
