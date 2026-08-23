from unittest.mock import patch, ANY, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@patch("analytics.redis_client")
def test_games_cache_hit(mock_redis_client):
    cached_data = '[{"game_id": "cached_game", "event_count": 10}]'
    mock_redis_client.get.return_value = cached_data

    response = client.get("/games")

    assert response.status_code == 200
    assert response.json() == [
        {
            "game_id": "cached_game",
            "event_count": 10,
        }
    ]
    mock_redis_client.get.assert_called_once_with("games:statistics")


@patch("analytics.get_db_connection")
@patch("analytics.redis_client")
def test_games_cache_expiration(mock_redis_client, mock_get_db):
    # 1. Mock DB to prevent PostgreSQL connections
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor
    mock_get_db.return_value = mock_conn

    # 2. Mock Redis cache miss
    mock_redis_client.get.return_value = None

    response = client.get("/games")

    assert response.status_code == 200
    mock_redis_client.get.assert_called_once_with("games:statistics")


@patch("analytics.get_db_connection")
@patch("analytics.redis_client")
def test_games_result_is_cached(mock_redis_client, mock_get_db):
    # 1. Mock DB to prevent PostgreSQL connections
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor
    mock_get_db.return_value = mock_conn

    # 2. Mock Redis cache miss
    mock_redis_client.get.return_value = None

    response = client.get("/games")

    assert response.status_code == 200
    mock_redis_client.set.assert_called_once()


@patch("analytics.get_db_connection")
@patch("analytics.redis_client")
def test_games_result_cached_for_60_seconds(mock_redis_client, mock_get_db):
    # 1. Mock DB to prevent PostgreSQL connections
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor
    mock_get_db.return_value = mock_conn

    # 2. Mock Redis cache miss
    mock_redis_client.get.return_value = None

    client.get("/games")

    mock_redis_client.set.assert_called_once_with(
        name="games:statistics",
        value=ANY,
        ex=60,
    )