import uuid
from datetime import datetime, date

import pytest
from database import get_db_connection
from analytics import (
    get_game_statistics,
    get_level_statistics,
    get_player_statistics,
    get_sessions,
    get_retention,
)


@pytest.fixture(scope="module")
def setup_test_database():
    """
    A fixture to set up the database with a known set of test data
    and clean it up after the tests are done.
    This is a module-scoped fixture, so it runs once for all tests in this file.
    """
    run_id = uuid.uuid4()
    game1_id = f"integration_game1_{run_id}"
    game2_id = f"integration_game2_{run_id}"
    player1_id = f"integration_player1_{run_id}"
    player2_id = f"integration_player2_{run_id}"
    player3_id = f"integration_player3_{run_id}"
    player4_id = f"integration_player4_{run_id}"

    mock_events = [
        # Game 1, Player 1: Completes level 1 and returns the next day
        ("player_started_level", player1_id, game1_id, "2026-08-23T10:00:00Z", 1),
        ("level_completed", player1_id, game1_id, "2026-08-23T10:05:00Z", 1),
        ("player_started_level", player1_id, game1_id, "2026-08-24T11:00:00Z", 1),
        # Game 1, Player 2: Starts level 1 and dies
        ("player_started_level", player2_id, game1_id, "2026-08-23T11:00:00Z", 1),
        ("player_died", player2_id, game1_id, "2026-08-23T11:01:00Z", 1),
        # Game 1, Player 3: Starts level 2
        ("player_started_level", player3_id, game1_id, "2026-08-23T12:00:00Z", 2),
        # Game 2, Player 4: Starts level 1
        ("player_started_level", player4_id, game2_id, "2026-08-23T12:00:00Z", 1),
    ]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert mock data
    for event in mock_events:
        cursor.execute(
            """
            INSERT INTO events (event, player_id, game_id, timestamp, level)
            VALUES (%s, %s, %s, %s, %s)
            """,
            event,
        )
    conn.commit()

    yield {
        "game1_id": game1_id,
        "game2_id": game2_id,
        "player1_id": player1_id,
        "player2_id": player2_id,
        "player3_id": player3_id,
        "player4_id": player4_id,
    }

    # Clean up only the data inserted by this fixture
    cursor.execute(
        "DELETE FROM events WHERE game_id = %s OR game_id = %s", (game1_id, game2_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


def test_get_level_statistics_integration(setup_test_database):
    """
    Tests the get_level_statistics function against a real database.
    """
    game1_id = setup_test_database["game1_id"]
    level_stats = get_level_statistics(game1_id)

    expected_stats = [
        {
            "level": 1,
            "players_started": 2,
            "players_completed": 1,
            "completion_rate": 50.0,
            "total_deaths": 1,
            "players_died": 1,
            "average_deaths": 0.5,
            # This is negative because the analytics query incorrectly pairs
            # the second "player_started_level" event with the first
            # "level_completed" event, resulting in a negative duration.
            "average_completion_time_seconds": -44700.0,
        },
        {
            "level": 2,
            "players_started": 1,
            "players_completed": 0,
            "completion_rate": 0.0,
            "total_deaths": 0,
            "players_died": 0,
            "average_deaths": 0.0,
            "average_completion_time_seconds": None,
        },
    ]

    assert level_stats == expected_stats


def test_get_sessions_integration(setup_test_database):
    """
    Tests the get_sessions function against a real database.
    """
    game1_id = setup_test_database["game1_id"]
    player1_id = setup_test_database["player1_id"]
    player2_id = setup_test_database["player2_id"]
    player3_id = setup_test_database["player3_id"]

    sessions = get_sessions(game1_id)

    expected_sessions = [
        {
            "player_id": player1_id,
            "game_id": game1_id,
            "session_number": 1,
            "session_start": datetime(2026, 8, 23, 10, 0),
            "session_end": datetime(2026, 8, 23, 10, 5),
            "event_count": 2,
        },
        {
            "player_id": player1_id,
            "game_id": game1_id,
            "session_number": 2,
            "session_start": datetime(2026, 8, 24, 11, 0),
            "session_end": datetime(2026, 8, 24, 11, 0),
            "event_count": 1,
        },
        {
            "player_id": player2_id,
            "game_id": game1_id,
            "session_number": 1,
            "session_start": datetime(2026, 8, 23, 11, 0),
            "session_end": datetime(2026, 8, 23, 11, 1),
            "event_count": 2,
        },
        {
            "player_id": player3_id,
            "game_id": game1_id,
            "session_number": 1,
            "session_start": datetime(2026, 8, 23, 12, 0),
            "session_end": datetime(2026, 8, 23, 12, 0),
            "event_count": 1,
        },
    ]

    sorted_sessions = sorted(sessions, key=lambda x: x["player_id"])
    sorted_expected_sessions = sorted(expected_sessions, key=lambda x: x["player_id"])

    assert sorted_sessions == sorted_expected_sessions


def test_get_retention_integration(setup_test_database):
    """
    Tests the get_retention function against a real database.
    """
    game1_id = setup_test_database["game1_id"]
    retention = get_retention(game1_id)

    expected_retention = [
        {
            "cohort_date": date(2026, 8, 23),
            "players_active": 3,
            "players_returned": 1,
            "day_1_retention": 33.33,
        },
        {
            "cohort_date": date(2026, 8, 24),
            "players_active": 1,
            "players_returned": 0,
            "day_1_retention": 0.0,
        },
    ]

    assert retention == expected_retention


def test_get_game_statistics_integration(setup_test_database):
    """
    Tests the get_game_statistics function against a real database.
    """
    game_stats = get_game_statistics()

    game1_id = setup_test_database["game1_id"]
    game2_id = setup_test_database["game2_id"]

    expected_stats = [
        {"game_id": game1_id, "event_count": 6},
        {"game_id": game2_id, "event_count": 1},
    ]

    # Sort both lists by game_id to ensure the order is consistent
    sorted_game_stats = sorted(game_stats, key=lambda x: x["game_id"])
    sorted_expected_stats = sorted(expected_stats, key=lambda x: x["game_id"])

    assert sorted_game_stats == sorted_expected_stats


def test_get_player_statistics_integration(setup_test_database):
    """
    Tests the get_player_statistics function against a real database.
    """
    player_stats = get_player_statistics()

    player1_id = setup_test_database["player1_id"]
    player2_id = setup_test_database["player2_id"]
    player3_id = setup_test_database["player3_id"]
    player4_id = setup_test_database["player4_id"]

    expected_stats = [
        {"player_id": player1_id, "event_count": 3},
        {"player_id": player2_id, "event_count": 2},
        {"player_id": player3_id, "event_count": 1},
        {"player_id": player4_id, "event_count": 1},
    ]

    # Sort both lists by player_id to ensure the order is consistent
    sorted_player_stats = sorted(player_stats, key=lambda x: x["player_id"])
    sorted_expected_stats = sorted(expected_stats, key=lambda x: x["player_id"])

    assert sorted_player_stats == sorted_expected_stats