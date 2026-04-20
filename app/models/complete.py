from pydantic import BaseModel

class CompleteRequest(BaseModel):
    assignment_id: int
    truck_id: str