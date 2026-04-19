from pydantic import BaseModel, field_validator
from typing import Literal

# Valid truck types aligned with TruckIT moving platform
TruckType = Literal[
    "cargo_van",
    "small_truck",
    "medium_truck",
    "large_truck",
    "specialty_truck"
]

# Service types from user stories (CUS-05)
ServiceType = Literal[
    "packing",
    "loading",
    "full_move"
]


class MoveRequest(BaseModel):
    customer_id: str
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    truck_type: TruckType
    service_type: ServiceType

    @field_validator("pickup_lat", "dropoff_lat")
    @classmethod
    def validate_lat(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("pickup_lng", "dropoff_lng")
    @classmethod
    def validate_lng(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v