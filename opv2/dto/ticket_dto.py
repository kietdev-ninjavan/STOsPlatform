from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List

from stos.utils import parse_datetime
from ..base.ticket import TicketStatusChoices, TicketTypeChoices, TicketSubTypeChoices


@dataclass
class TicketResolveDTO:
    tracking_id: str
    ticket_id: int
    custom_fields: List[str]
    order_outcome: str
    new_instruction: str
    rts_reason: Optional[str] = None
    reporter_email: str = 'vn-nightops@ninjavan.co'
    ticket_status: str = 'RESOLVED'

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TicketDTO:
    created_at: datetime
    hub_id: int
    id: int
    investigating_hub_id: int
    source_of_entry: str
    status: TicketStatusChoices
    type: TicketTypeChoices
    sub_type: TicketSubTypeChoices
    tracking_id: str

    @classmethod
    def from_dict(cls, data: dict):
        """Create an OrderDTO from a dictionary"""
        return cls(
            id=data.get('id'),
            hub_id=int(data.get('hubId')),
            created_at=parse_datetime(data.get('createdAt')),
            investigating_hub_id=data.get('investigatingHubId'),
            source_of_entry=data.get('sourceOfEntry'),
            status=data.get('status'),
            type=data.get('ticketTypeId'),
            sub_type=data.get('subTicketTypeId'),
            tracking_id=data.get('trackingId')
        )

    def __repr__(self):
        return self.id
