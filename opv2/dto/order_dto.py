import datetime
import json
from dataclasses import dataclass
from typing import Optional, Any, List

from stos.utils import parse_datetime


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
    mps_id: Optional[int] = None
    mps_sequence_number: Optional[int] = None

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
            mps_id=data.get('mps_id'),
            mps_sequence_number=data.get('mps_sequence_number')
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


@dataclass
class AddressDTO:
    rts: bool
    postcode: str
    district: str
    city: str
    state: str
    country: str
    latitude: float
    longitude: float
    order_id: int
    waypoint_id: int
    tracking_id: str
    created_at: datetime
    address_one: str
    address_two: str
    zone_id: int
    hub_id: int
    av_status: str
    av_mode: str
    av_source: str
    shipper_id: int
    marketplace_id: int
    global_shipper_id: int
    master_shipper_id: int
    address_type: str

    @classmethod
    def form_dict(cls, data: dict):
        return cls(
            rts=data.get('rts'),
            postcode=data.get('postcode'),
            district=data.get('district'),
            city=data.get('city'),
            state=data.get('state'),
            country=data.get('country'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            order_id=data.get('order_id'),
            waypoint_id=data.get('waypoint_id'),
            tracking_id=data.get('tracking_number'),
            created_at=parse_datetime(data.get('created_at')),
            address_one=data.get('address_one'),
            address_two=data.get('address_two'),
            zone_id=data.get('zone_id'),
            hub_id=data.get('zone_hub_id'),
            av_status=data.get('av_status'),
            av_mode=data.get('av_mode'),
            av_source=data.get('av_source'),
            shipper_id=data.get('shipper_id'),
            marketplace_id=data.get('marketplace_id'),
            global_shipper_id=data.get('global_shipper_id'),
            master_shipper_id=data.get('master_shipper_id'),
            address_type=data.get('address_type')
        )


@dataclass
class BulkAVDTO:
    waypoint: int
    latitude: float
    longitude: float

    def to_dict(self) -> dict:
        return {
            'id': self.waypoint,
            'latitude': self.latitude,
            'longitude': self.longitude
        }