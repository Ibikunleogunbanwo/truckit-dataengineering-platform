from fastapi import APIRouter
from app.services.producer import send_move_request
from app.models.move import MoveRequest

router = APIRouter()

@router.post("/truck/move/request")
def create_move(request: MoveRequest):
    send_move_request(request.dict())
    return {"status": "move request sent to Kafka"}