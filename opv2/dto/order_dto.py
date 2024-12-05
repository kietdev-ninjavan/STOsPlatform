import json
from dataclasses import dataclass
from typing import Optional, Any, List


@dataclass
class OrderDTO:
    id: int
    tracking_id: Optional[str]
    granular_status: str
    status: str
    shipper_id: int
    type: str
    is_rts: bool
    full_address: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    ward: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict):
        """Create an OrderDTO from a dictionary"""
        address1 = data.get('to_address1') if data.get('to_address1') else ''
        address2 = data.get('to_address2') if data.get('to_address2') else ''
        return cls(
            id=data.get('id'),
            tracking_id=data.get('tracking_id'),
            granular_status=data.get('granular_status'),
            status=data.get('status'),
            shipper_id=data.get('global_shipper_id'),
            type=data.get('type'),
            is_rts=data.get('is_rts'),
            full_address=f"{address1} {address2}",
            province=data.get('to_state') if data.get('to_state') != '' else None,
            district=data.get('to_city') if data.get('to_city') != '' else None,
            ward=data.get('to_district') if data.get('to_district') != '' else None,
        )

    def __repr__(self):
        return self.tracking_id


@dataclass
class AllOrderSearchFilterDTO:
    field: str
    values: List[Any]

    def to_dict(self) -> dict:
        return {
            'field': self.field,
            'values': self.values
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
