import uuid
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from database import get_db_connection

# Use the TestClient for in-memory API requests
client = TestClient(app)


def setup_api_key(game_id, api_key):
    """Inserts a temporary API key into the database for a test."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO game_api_keys (game_id, api_key) VALUES (%s, %s)",
            (game_id, api_key),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def cleanup_db(game_id):
    """Removes a temporary API key from the database after a test."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM game_api_keys WHERE game_id = %s", (game_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


@patch("main.publish_event")
def test_valid_api_key(mock_publish):
    """
    Tests that a request with a valid API key is accepted and queued.
    """
    game_id = f"auth_test_game_{uuid.uuid4()}"
    api_key = f"auth_test_key_{uuid.uuid4()}"
    headers = {"X-API-Key": api_key}
    event = {
        "event": "test_event",
        "player_id": "p1",
        "game_id": game_id,
        "timestamp": "2026-01-01T00:00:00",
        "level": 1,
    }

    setup_api_key(game_id, api_key)

    try:
        response = client.post("/events", json=event, headers=headers)
        assert response.status_code == 200
        mock_publish.assert_called_once()
    finally:
        cleanup_db(game_id)


@patch("main.publish_event")
def test_missing_api_key(mock_publish):
    """
    Tests that a request without an API key is rejected and not queued.
    """
    event = {
        "event": "test_event",
        "player_id": "p1",
        "game_id": "some_game",
        "timestamp": "2026-01-01T00:00:00",
        "level": 1,
    }
    response = client.post("/events", json=event)
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API key"
    mock_publish.assert_not_called()


@patch("main.publish_event")
def test_invalid_api_key(mock_publish):
    """
    Tests that a request with an invalid API key is rejected and not queued.
    """
    headers = {"X-API-Key": "this-key-is-invalid"}
    event = {
        "event": "test_event",
        "player_id": "p1",
        "game_id": "some_game",
        "timestamp": "2026-01-01T00:00:00",
        "level": 1,
    }
    response = client.post("/events", json=event, headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"
    mock_publish.assert_not_called()


@patch("main.publish_event")
def test_api_key_wrong_game(mock_publish):
    """
    Tests that a key for one game is not valid for another, and the event is not queued.
    """
    game_id_1 = f"auth_test_game_{uuid.uuid4()}"
    game_id_2 = f"auth_test_game_{uuid.uuid4()}"
    api_key_1 = f"auth_test_key_{uuid.uuid4()}"
    headers = {"X-API-Key": api_key_1}

    # API key is valid for game_id_1, but the event is for game_id_2
    event = {
        "event": "test_event",
        "player_id": "p1",
        "game_id": game_id_2,
        "timestamp": "2026-01-01T00:00:00",
        "level": 1,
    }

    setup_api_key(game_id_1, api_key_1)

    try:
        response = client.post("/events", json=event, headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid API key"
        mock_publish.assert_not_called()
    finally:
        cleanup_db(game_id_1)