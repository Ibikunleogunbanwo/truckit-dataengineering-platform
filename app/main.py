from fastapi import FastAPI
from app.api.moves import router as move_router
from app.api.complete import router as complete_router

app = FastAPI(title="TruckIT Streaming Platform")

app.include_router(move_router)
app.include_router(complete_router)