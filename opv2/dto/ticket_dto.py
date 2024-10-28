from dataclasses import dataclass, field, asdict
from typing import Optional, List

from ..base.ticket import TicketStatusChoices


@dataclass
class TicketResolveDTO:
    tracking_id: str
    ticket_id: int
    custom_fields: List[str]
    order_outcome: str
    new_instruction: str
    rts_reason: Optional[str] = None
    reporter_email: str = 'vn-nightops@ninjavan.co'
    ticket_status: TicketStatusChoices = field(default=TicketStatusChoices.RESOLVED, init=False)

    def to_dict(self) -> dict:
        return asdict(self)
