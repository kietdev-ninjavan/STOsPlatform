from dataclasses import dataclass


@dataclass
class ShipperDTO:
    id: int
    legacy_id: int
    name: str
    email: str
    industry_id: int
    liaison_name: str
    liaison_email: str
    liaison_address: str
    liaison_postcode: str
    contact: str
    sales_person: str
    active: bool
    created_at: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            legacy_id=data["legacy_id"],
            name=data["name"],
            email=data["email"],
            industry_id=data["industry_id"],
            liaison_name=data["liaison_name"],
            liaison_email=data["liaison_email"],
            liaison_address=data["liaison_address"],
            liaison_postcode=data["liaison_postcode"],
            contact=data["contact"],
            sales_person=data["sales_person"],
            active=data["active"],
            created_at=data["created_at"]
        )
