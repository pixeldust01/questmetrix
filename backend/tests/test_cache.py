from unittest.mock import patch, ANY
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_games_cache_hit():
    cached_data = '[{"game_id": "cached_game", "event_count": 10}]'

    with patch(
        "analytics.redis_client.get",
        return_value=cached_data,
    ):
        response = client.get("/games")

    assert response.status_code == 200
    assert response.json() == [
        {
            "game_id": "cached_game",
            "event_count": 10,
        }
    ]

def test_games_cache_expiration():
    with patch(
        "analytics.redis_client.get",
        return_value=None,
    ) as mock_get:
        response = client.get("/games")

    assert response.status_code == 200

    mock_get.assert_called_once_with("games:statistics")

def test_games_result_is_cached():
    with patch(
        "analytics.redis_client.get",
        return_value=None,
    ), patch(
        "analytics.redis_client.set"
    ) as mock_set:
        response = client.get("/games")

    assert response.status_code == 200

    mock_set.assert_called_once()

def test_games_result_cached_for_60_seconds():
    with patch(
        "analytics.redis_client.get",
        return_value=None,
    ), patch(
        "analytics.redis_client.set"
    ) as mock_set:
        client.get("/games")

    mock_set.assert_called_once_with(
        name="games:statistics",
        value=ANY,
        ex=60,
    )

def test_event_creation_invalidates_games_cache():
    with patch(
        "events.redis_client.delete"
    ) as mock_delete:

        event = {
            "event": "enemy_killed",
            "player_id": "pytest_cache_player",
            "game_id": "pytest_game",
            "timestamp": "2026-08-13T15:00:00",
            "level": 1,
        }

        response = client.post("/events", json=event)

    assert response.status_code == 200

    mock_delete.assert_called_once_with("games:statistics")