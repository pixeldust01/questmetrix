from fastapi.testclient import TestClient
from main import app
from database import get_db_connection
import time

client = TestClient(app)

def test_event_persists_to_database():
    # 1. Post real event to API
    event = {"event": "e2e_test", "player_id": "p1", "game_id": "g1", "timestamp": "2026-01-01T00:00:00", "level": 1}
    response = client.post("/events", json=event)
    assert response.status_code == 200
    
    # 2. Wait for background worker to process queue
    time.sleep(10)
    
    # 3. Query real database to verify persistence
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE player_id = 'p1'")
    results = cursor.fetchall()
    assert len(results) > 0