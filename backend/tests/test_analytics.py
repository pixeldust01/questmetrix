from fastapi.testclient import TestClient
from database import get_db_connection
from main import app

client = TestClient(app)


def test_get_levels(mock_analytics_data):
    response = client.get(
        "/levels",
        params={"game_id": "pytest_analytics_game"}
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    level_1 = data[0]

    assert level_1["level"] == 1
    assert level_1["players_started"] == 2
    assert level_1["players_completed"] == 2
    assert level_1["completion_rate"] == 100.0
    assert level_1["total_deaths"] == 0
    assert level_1["players_died"] == 0
    assert level_1["average_deaths"] == 0.0
    assert level_1["average_completion_time_seconds"] == 450.0

    level_2 = data[1]

    assert level_2["level"] == 2
    assert level_2["players_started"] == 2
    assert level_2["players_completed"] == 2
    assert level_2["completion_rate"] == 100.0
    assert level_2["total_deaths"] == 1
    assert level_2["players_died"] == 1
    assert level_2["average_deaths"] == 0.5
    assert level_2["average_completion_time_seconds"] == 600.0

def test_get_levels_unknown_game():
    response = client.get(
        "/levels",
        params={"game_id": "game_that_does_not_exist"}
    )

    assert response.status_code == 200
    assert response.json() == []

def test_get_games():
    response = client.get("/games")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

def test_get_players():
    response = client.get("/players")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

def test_get_sessions(session_test_data):
    response = client.get(
        "/sessions",
        params={"game_id": "pytest_session_game"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    first_session = data[0]

    assert first_session["player_id"] == "session_test_player"
    assert first_session["game_id"] == "pytest_session_game"
    assert first_session["session_number"] == 1
    assert first_session["event_count"] == 3

    second_session = data[1]

    assert second_session["player_id"] == "session_test_player"
    assert second_session["game_id"] == "pytest_session_game"
    assert second_session["session_number"] == 2
    assert second_session["event_count"] == 2

def test_get_retention(retention_test_data):
    response = client.get(
        "/retention",
        params={"game_id": "pytest_retention_game"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    day_zero = data[0]

    assert day_zero["cohort_date"] == "2026-09-01"
    assert day_zero["players_active"] == 4
    assert day_zero["players_returned"] == 2
    assert day_zero["day_1_retention"] == 50.0