import pytest
from datetime import datetime, date
from database import get_db_connection
from analytics import (
    get_game_statistics,
    get_level_statistics,
    get_player_statistics,
    get_sessions,
    get_retention,
)

# A known set of events to test against
MOCK_EVENTS = [
    # Game 1: Player 1 completes a level
    (
        "player_started_level",
        "player1",
        "game1",
        "2026-08-23T10:00:00Z",
        1,
    ),
    (
        "level_completed",
        "player1",
        "game1",
        "2026-08-23T10:05:00Z",
        1,
    ),
    # Game 1: Player 2 dies
    (
        "player_started_level",
        "player2",
        "game1",
        "2026-08-23T11:00:00Z",
        1,
    ),
    ("player_died", "player2", "game1", "2026-08-23T11:01:00Z", 1),
    # Game 2: A single event
    ("player_started_level", "player1", "game2", "2026-08-23T12:00:00Z", 1),
]


@pytest.fixture(scope="module")
def setup_test_database():
    """
    A fixture to set up the database with a known set of test data
    and clean it up after the tests are done.
    This is a module-scoped fixture, so it runs once for all tests in this file.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clean up before starting
    cursor.execute("TRUNCATE TABLE events RESTART IDENTITY;")

    # Insert mock data
    for event in MOCK_EVENTS:
        cursor.execute(
            """
            INSERT INTO events (event, player_id, game_id, timestamp, level)
            VALUES (%s, %s, %s, %s, %s)
            """,
            event,
        )
    conn.commit()

    yield # This is where the tests will run

    # Clean up after all tests in the module are done
    cursor.execute("TRUNCATE TABLE events RESTART IDENTITY;")
    conn.commit()
    cursor.close()
    conn.close()


def test_get_level_statistics_integration(setup_test_database):
    """
    Tests the get_level_statistics function against a real database.
    """
    # The function under test
    level_stats = get_level_statistics("game1")

    # Expected result based on MOCK_EVENTS for game1
    expected_stats = [
        {
            "level": 1,
            "players_started": 2,
            "players_completed": 1,
            "completion_rate": 50.0,
            "total_deaths": 1,
            "players_died": 1,
            "average_deaths": 0.5,
            "average_completion_time_seconds": None
        }
    ]

    assert level_stats == expected_stats


def test_get_sessions_integration(setup_test_database):
    """
    Tests the get_sessions function against a real database.
    """
    # The function under test
    sessions = get_sessions("game1")

    # Expected result based on MOCK_EVENTS for game1
    expected_sessions = [
        {
            "player_id": "player1",
            "game_id": "game1",
            "session_number": 1,
            "session_start": datetime(2026, 8, 23, 10, 0),
            "session_end": datetime(2026, 8, 23, 10, 5),
            "event_count": 2
        },
        {
            "player_id": "player2",
            "game_id": "game1",
            "session_number": 1,
            "session_start": datetime(2026, 8, 23, 11, 0),
            "session_end": datetime(2026, 8, 23, 11, 1),
            "event_count": 2
        }
    ]

    # Sort both lists by player_id to ensure comparison is consistent
    sorted_sessions = sorted(sessions, key=lambda x: x["player_id"])
    sorted_expected_sessions = sorted(expected_sessions, key=lambda x: x["player_id"])

    assert sorted_sessions == sorted_expected_sessions


def test_get_retention_integration(setup_test_database):
    """
    Tests the get_retention function against a real database.
    """
    # The function under test
    retention = get_retention("game1")

    # Expected result based on MOCK_EVENTS for game1
    # In this limited data set, no players return on subsequent days.
    expected_retention = [
        {
            "cohort_date": date(2026, 8, 23),
            "players_active": 2,
            "players_returned": 0,
            "day_1_retention": 0.0
        }
    ]

    assert retention == expected_retention