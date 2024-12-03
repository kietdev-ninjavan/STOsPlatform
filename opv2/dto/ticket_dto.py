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
    hub_id: Optional[int]
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
            hub_id=int(data.get('hubId')) if data.get('hubId') != '' else None,
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


@dataclass
class CancelTicketDTO:
    custom_fields: list
    ticket_id: int
    tracking_id: str
    investigating_hub_id: int
    reporter_email: str = 'vn-nightops@ninjavan.co'
    ticket_status: str = 'CANCELLED'

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TicketCreateDTO:
    tracking_id: str
    type: TicketTypeChoices
    sub_type: Optional[TicketSubTypeChoices]
    investigating_hub_id: int
    investigating_group: str
    assignee_email: Optional[str]
    ticket_notes: Optional[str]
    entry_source: str = 'GN'

    def to_dict(self) -> dict:
        return {
            'tracking_id': self.tracking_id,
            'type': self.type.label,
            'sub_type': self.sub_type.label if self.sub_type else None,
            'investigating_group': self.investigating_group,
            'assignee_email': self.assignee_email if self.assignee_email else 'vn-nightops@ninjavan.co',
            'investigating_hub_id': self.investigating_hub_id,
            'entry_source': self.entry_source,
            'ticket_notes': self.ticket_notes
        }
