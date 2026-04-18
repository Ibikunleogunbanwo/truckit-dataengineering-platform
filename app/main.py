from fastapi import FastAPI
from app.api.moves import router as move_router

app = FastAPI(title="TruckIT Streaming Platform")

app.include_router(move_router)