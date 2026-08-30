import uuid
import pytest
from redis_client import redis_client
from datetime import datetime, date
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
    game3_id = f"integration_game3_{run_id}"
    player1_id = f"integration_player1_{run_id}"
    player2_id = f"integration_player2_{run_id}"
    player3_id = f"integration_player3_{run_id}"
    player4_id = f"integration_player4_{run_id}"
    player5_id = f"integration_player5_{run_id}"
    player6_id = f"integration_player6_{run_id}"

    mock_events = [
        # Game 1, Player 1: Completes level 1 and returns the next day
        ("player_started_level", player1_id, game1_id, "2026-08-23T10:00:00", 1),
        ("level_completed", player1_id, game1_id, "2026-08-23T10:05:00", 1),
        ("player_started_level", player1_id, game1_id, "2026-08-24T11:00:00", 1),
        # Game 1, Player 2: Starts level 1 and dies
        ("player_started_level", player2_id, game1_id, "2026-08-23T11:00:00", 1),
        ("player_died", player2_id, game1_id, "2026-08-23T11:01:00", 1),
        # Game 1, Player 3: Starts level 2
        ("player_started_level", player3_id, game1_id, "2026-08-23T12:00:00", 2),
        # Game 2, Player 4: Starts level 1
        ("player_started_level", player4_id, game2_id, "2026-08-23T12:00:00", 1),
        # Game 1, Player 5: Tests session boundaries
        ("player_started_level", player5_id, game1_id, "2026-08-25T10:00:00", 1),
        ("player_died", player5_id, game1_id, "2026-08-25T10:29:00", 1),
        ("player_started_level", player5_id, game1_id, "2026-08-25T11:00:00", 1),
        ("player_died", player5_id, game1_id, "2026-08-25T11:01:00", 1),
        # Game 1, Player 6: Starts and never returns
        ("player_started_level", player6_id, game1_id, "2026-08-26T10:00:00", 1),
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
        "game3_id": game3_id,
        "player1_id": player1_id,
        "player2_id": player2_id,
        "player3_id": player3_id,
        "player4_id": player4_id,
        "player5_id": player5_id,
        "player6_id": player6_id,
    }

    # Clean up only the data inserted by this fixture
    cursor.execute(
        "DELETE FROM events WHERE game_id = ANY(%s)", ([game1_id, game2_id, game3_id],)
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
            "players_started": 4,
            "players_completed": 1,
            "completion_rate": 25.00,
            "total_deaths": 3,
            "players_died": 2,
            "average_deaths": 0.75,
            "average_completion_time_seconds": 300.0,
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
    player5_id = setup_test_database["player5_id"]
    player6_id = setup_test_database["player6_id"]

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
        {
            "player_id": player5_id,
            "game_id": game1_id,
            "session_number": 1,
            "session_start": datetime(2026, 8, 25, 10, 0),
            "session_end": datetime(2026, 8, 25, 10, 29),
            "event_count": 2,
        },
        {
            "player_id": player5_id,
            "game_id": game1_id,
            "session_number": 2,
            "session_start": datetime(2026, 8, 25, 11, 0),
            "session_end": datetime(2026, 8, 25, 11, 1),
            "event_count": 2,
        },
        {
            "player_id": player6_id,
            "game_id": game1_id,
            "session_number": 1,
            "session_start": datetime(2026, 8, 26, 10, 0),
            "session_end": datetime(2026, 8, 26, 10, 0),
            "event_count": 1,
        },
    ]

    sorted_sessions = sorted(sessions, key=lambda x: (x["player_id"], x["session_number"]))
    sorted_expected_sessions = sorted(expected_sessions, key=lambda x: (x["player_id"], x["session_number"]))

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
        {
            "cohort_date": date(2026, 8, 25),
            "players_active": 1,
            "players_returned": 0,
            "day_1_retention": 0.0,
        },
        {
            "cohort_date": date(2026, 8, 26),
            "players_active": 1,
            "players_returned": 0,
            "day_1_retention": 0.0,
        },
    ]

    assert retention == expected_retention


def test_get_retention_no_players():
    """
    Tests the get_retention function for a game with no players.
    """
    retention = get_retention("non_existent_game")
    assert retention == []


def test_get_retention_for_game_with_no_events(setup_test_database):
    """
    Tests get_retention for a game with no telemetry events.
    """
    game3_id = setup_test_database["game3_id"]
    retention = get_retention(game3_id)
    assert retention == []


def test_get_game_statistics_integration(setup_test_database):
    """
    Tests the get_game_statistics function against a real database.
    """
    game1_id = setup_test_database["game1_id"]
    game2_id = setup_test_database["game2_id"]
    game3_id = setup_test_database["game3_id"]

    # Invalidate cache to prevent stale data from previous test runs
    redis_client.delete("games:statistics")

    # Filter by the fixture's game IDs
    game_stats = get_game_statistics(game_ids=[game1_id, game2_id, game3_id])

    expected_stats = [
        {"game_id": game1_id, "event_count": 11},
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
    game1_id = setup_test_database["game1_id"]
    game2_id = setup_test_database["game2_id"]
    
    # Filter by the fixture's game IDs to isolate players
    player_stats = get_player_statistics(game_ids=[game1_id, game2_id])

    player1_id = setup_test_database["player1_id"]
    player2_id = setup_test_database["player2_id"]
    player3_id = setup_test_database["player3_id"]
    player4_id = setup_test_database["player4_id"]
    player5_id = setup_test_database["player5_id"]
    player6_id = setup_test_database["player6_id"]

    expected_stats = [
        {"player_id": player1_id, "event_count": 3},
        {"player_id": player2_id, "event_count": 2},
        {"player_id": player3_id, "event_count": 1},
        {"player_id": player4_id, "event_count": 1},
        {"player_id": player5_id, "event_count": 4},
        {"player_id": player6_id, "event_count": 1},
    ]

    # Sort both lists by player_id to ensure the order is consistent
    sorted_player_stats = sorted(player_stats, key=lambda x: x["player_id"])
    sorted_expected_stats = sorted(expected_stats, key=lambda x: x["player_id"])

    assert sorted_player_stats == sorted_expected_stats


def test_get_level_statistics_no_events():
    result = get_level_statistics("non_existent_game")
    assert result == []


def test_get_sessions_no_events():
    result = get_sessions("non_existent_game")
    assert result == []


def test_get_player_statistics_no_events():
    result = get_player_statistics(
        game_ids=["non_existent_game"]
    )
    assert result == []