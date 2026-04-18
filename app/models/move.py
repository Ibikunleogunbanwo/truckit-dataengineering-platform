from pydantic import BaseModel

class MoveRequest(BaseModel):
    customer_id: str
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float

