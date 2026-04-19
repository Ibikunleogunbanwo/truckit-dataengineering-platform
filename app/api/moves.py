from fastapi import APIRouter, HTTPException
from app.services.producer import send_move_request
from app.models.move import MoveRequest

router = APIRouter()

@router.post("/truck/move/request", status_code=202)
def create_move(request: MoveRequest):
    try:
        send_move_request(request.model_dump())
        return {"status": "move request sent to Kafka"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to send move request: {str(e)}")