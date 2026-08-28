import os
import uuid
import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
TEST_GAME_ID = f"rate_limit_game_{uuid.uuid4()}"
TEST_PLAYER_ID = f"rate_limit_player_{uuid.uuid4()}"


def test_event_rate_limit():
    event = {
        "event": "rate_limit_test",
        "player_id": TEST_PLAYER_ID,
        "game_id": TEST_GAME_ID,
        "timestamp": "2026-08-28T12:00:00",
        "level": 1,
    }

    for _ in range(100):
        response = requests.post(f"{BASE_URL}/events", json=event)
        assert response.status_code == 200

    response = requests.post(f"{BASE_URL}/events", json=event)
    assert response.status_code == 429