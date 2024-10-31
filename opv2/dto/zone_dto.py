from dataclasses import dataclass


@dataclass
class ZoneDTO:
    id: int
    legacy_zone_id: int
    name: str
    type: str
    hub_id: int
    short_name: str
    description: str
    latitude: float
    longitude: float

    @classmethod
    def from_dict(cls, data: dict):
        """Create an OrderDTO from a dictionary"""
        return cls(
            id=data.get('id'),
            legacy_zone_id=data.get('legacy_zone_id'),
            name=data.get('name'),
            type=data.get('type'),
            hub_id=data.get('hub_id'),
            short_name=data.get('short_name'),
            description=data.get('description'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )

    def __repr__(self):
        return self.name
