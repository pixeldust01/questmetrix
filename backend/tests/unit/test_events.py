from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime
from main import app

client = TestClient(app)


@patch("main.verify_api_key")
@patch("main.publish_event")
def test_create_event_queues_event(mock_publish, mock_verify_api_key):
    mock_publish.return_value = "1234567890-0"
    event = {
        "event": "enemy_killed",
        "player_id": "test_player",
        "game_id": "test_game",
        "timestamp": "2026-08-23T01:00:00",
        "level": 1,
    }
    response = client.post("/events", json=event)
    assert response.status_code == 200
    assert response.json() == {
        "message": "Event queued successfully!",
        "message_id": "1234567890-0",
        "event": event,
    }
    event["timestamp"] = datetime(2026, 8, 23, 1, 0, 0)
    mock_publish.assert_called_once_with(event)
    mock_verify_api_key.assert_called_once_with(event["game_id"], None)


@patch("main.verify_api_key")
@patch("main.publish_event")
@patch("events.get_db_connection")
def test_create_event_does_not_write_to_database(
    mock_get_db, mock_publish, mock_verify_api_key
):
    mock_publish.return_value = "1234567890-0"
    event = {
        "event": "enemy_killed",
        "player_id": "test_player",
        "game_id": "test_game",
        "timestamp": "2026-08-23T01:00:00",
        "level": 1,
    }

    response = client.post("/events", json=event)

    assert response.status_code == 200
    mock_get_db.assert_not_called()
    mock_verify_api_key.assert_called_once_with(event["game_id"], None)


def test_create_event_missing_required_fields():
    event = {"event": "enemy_killed"}

    response = client.post("/events", json=event)

    assert response.status_code == 422


def test_create_event_invalid_level():
    event = {
        "event": "enemy_killed",
        "player_id": "pytest_player",
        "game_id": "pytest_game",
        "timestamp": "2026-08-13T15:00:00",
        "level": "not_-number",
    }

    response = client.post("/events", json=event)

    assert response.status_code == 422