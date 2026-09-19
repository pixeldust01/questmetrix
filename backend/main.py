from datetime import datetime
import json
from fastapi import FastAPI, Request, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from events import create_event, get_all_events
from event_queue import publish_event
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from auth import verify_api_key
from websocket_manager import manager

limiter = Limiter(key_func=get_remote_address)

from analytics import (
    get_game_statistics,
    get_level_statistics,
    get_player_statistics,
    get_sessions,
    get_retention,
) 

app = FastAPI()
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Event(BaseModel):
    event: str
    player_id: str
    game_id: str
    timestamp: datetime
    level: int


@app.get("/")
def root():
    return {"message": "QuestMetrix backend is running!"}

@app.post("/events")
@limiter.limit("100/minute")
def create_event_endpoint(request: Request, event: Event,  x_api_key: str | None = Header(default=None)):
    verify_api_key(event.game_id, x_api_key)
    # event_id = create_event(event)

    event_data = event.model_dump()
    message_id = publish_event(event_data)

    return {
        "message": "Event queued successfully!",
        "event": event_data,
        "message_id": message_id,
    }

@app.get("/events")
def get_events():
    rows = get_all_events()

    return [
        {
            "id": row[0],
            "event": row[1],
            "player_id": row[2],
            "game_id": row[3],
            "timestamp": row[4],
            "level": row[5],
        }
        for row in rows
    ]

@app.get("/games")
def get_games():
    return get_game_statistics()

@app.get("/players")
def get_players():
    return get_player_statistics()

@app.get("/levels")
def get_levels(game_id: str):
    return get_level_statistics(game_id)

@app.get("/sessions")
def get_sessions_endpoint(game_id: str):
    return get_sessions(game_id)

@app.get("/retention")
def get_retention_endpoint(game_id: str):
    return get_retention(game_id)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            if message:
                event_data = json.loads(message)
                print(f"Received event shalalala: {event_data}")
            else:
                print("No event received shalalala")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
