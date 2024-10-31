from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from stos.utils import parse_datetime


@dataclass
class HubDTO:
    id: int
    name: str
    country: str
    city: Optional[str]
    latitude: float
    longitude: float
    region: Optional[str]
    area: Optional[str]
    active: bool
    short_name: Optional[str]
    sort_hub: bool
    facility_type: str
    opv2_created_at: datetime
    opv2_updated_at: datetime
    virtual_hub: bool
    parent_hub: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            name=data["name"],
            country=data["country"],
            city=data.get("city"),
            latitude=data["latitude"],
            longitude=data["longitude"],
            region=data.get("region"),
            area=data.get("area"),
            active=data["active"],
            short_name=data.get("short_name"),
            sort_hub=data["sort_hub"],
            facility_type=data["facility_type"],
            opv2_created_at=parse_datetime(data["created_at"]),
            opv2_updated_at=parse_datetime(data["updated_at"]),
            virtual_hub=data["virtual_hub"],
            parent_hub=data.get("parent_hub")
        )

    def __repr__(self):
        return self.name
