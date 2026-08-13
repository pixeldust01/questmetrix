from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_create_event():
    event = {
        "event": "enemy_killed",
        "player_id": "pytest_player",
        "game_id": "pytest_game",
        "timestamp": "2026-08-13T15:00:00",
        "level": 1
    }

    response = client.post("/events", json=event)

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Event stored successfully!"
    assert "id" in data


def test_created_event_can_be_retrieved():
    event = {
        "event": "enemy_killed",
        "player_id": "pytest_player",
        "game_id": "pytest_game",
        "timestamp": "2026-08-13T15:00:00",
        "level": 1
    }

    create_response = client.post(
        "/events",
        json=event
    )

    assert create_response.status_code == 200

    response = client.get("/events")

    assert response.status_code == 200

    events = response.json()

    matching_events = [
        event
        for event in events
        if event["player_id"] == "pytest_player"
        and event["game_id"] == "pytest_game"
    ]

    assert len(matching_events) == 1

    stored_event = matching_events[0]

    assert stored_event["event"] == "enemy_killed"
    assert stored_event["level"] == 1

def test_create_event_missing_required_fields():
    event = {
        "event": "enemy_killed"
    }

    response = client.post("/events", json=event)

    assert response.status_code == 422

def test_create_event_invalid_level():
    event = {
        "event": "enemy_killed",
        "player_id": "pytest_player",
        "game_id": "pytest_game",
        "timestamp": "2026-08-13T15:00:00",
        "level": "not_a_number"
    }

    response = client.post("/events", json=event)

    assert response.status_code == 422