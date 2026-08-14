from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_db_connection
from events import create_event, get_all_events

from analytics import (
    get_game_statistics,
    get_level_statistics,
    get_player_statistics,
    get_sessions,
    get_retention,
) 

app = FastAPI()
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
    timestamp: str
    level: int


@app.get("/")
def root():
    return {"message": "QuestMetrix backend is running!"}

@app.post("/events")
def create_event_endpoint(event: Event):
    event_id = create_event(event)

    return {
        "message": "Event stored successfully!",
        "id": event_id
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