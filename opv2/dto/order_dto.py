from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderDTO:
    id: int
    tracking_id: Optional[str]
    granular_status: str
    status: str
    shipper_id: int
    type: str
    is_rts: bool

    @classmethod
    def from_dict(cls, data: dict):
        """Create an OrderDTO from a dictionary"""
        return cls(
            id=data.get('id'),
            tracking_id=data.get('tracking_id'),
            granular_status=data.get('granular_status'),
            status=data.get('status'),
            shipper_id=data.get('global_shipper_id'),
            type=data.get('type'),
            is_rts=data.get('is_rts')
        )

    def __repr__(self):
        return self.tracking_id
