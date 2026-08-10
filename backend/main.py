import os
import psycopg2

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel


load_dotenv()

app = FastAPI()


class Event(BaseModel):
    event: str
    player_id: str
    game_id: str
    timestamp: str
    level: int


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


@app.get("/")
def root():
    return {"message": "QuestMetrix backend is running!"}


@app.post("/events")
def receive_event(event: Event):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO events (event, player_id, game_id, timestamp, level)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            event.event,
            event.player_id,
            event.game_id,
            event.timestamp,
            event.level
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Event stored successfully!",
        "event": event
    }