import uuid
import time

from fastapi.testclient import TestClient
from main import app
from database import get_db_connection


client = TestClient(app)

TEST_GAME_ID = f"e2e_game_{uuid.uuid4()}"
TEST_PLAYER_ID = f"e2e_player_{uuid.uuid4()}"


def test_event_persists_to_database():
    conn = get_db_connection()
    try:
        # 1. Post real event to API
        event = {
            "event": "e2e_test",
            "player_id": TEST_PLAYER_ID,
            "game_id": TEST_GAME_ID,
            "timestamp": "2026-01-01T00:00:00",
            "level": 1,
        }
        response = client.post("/events", json=event)
        assert response.status_code == 200

        # 2. Poll the database to verify persistence
        max_wait_time = 15  # seconds
        start_time = time.time()
        results = []
        while time.time() - start_time < max_wait_time:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE game_id = %s", (TEST_GAME_ID,))
            results = cursor.fetchall()
            if len(results) > 0:
                break
            time.sleep(1)  # Wait 1 second before retrying

        # 3. Assert that the event was found
        assert len(results) > 0

        # More specific assertions
        assert results[0][2] == TEST_PLAYER_ID
        assert results[0][3] == TEST_GAME_ID

    finally:
        # 4. Clean up the database
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE game_id = %s", (TEST_GAME_ID,))
        conn.commit()
        cursor.close()
        conn.close()