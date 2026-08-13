import pytest
from database import get_db_connection

@pytest.fixture(autouse=True)
def clean_test_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM events
        WHERE game_id IN (%s, %s, %s, %s);
        """,
        ("pytest_game", "pytest_analytics_game", "pytest_session_game", "pytest_retention_game"),
    )

    conn.commit()

    cursor.close()
    conn.close()

    yield

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM events
        WHERE game_id IN (%s, %s, %s, %s);
        """,
        ("pytest_game", "pytest_analytics_game", "pytest_session_game", "pytest_retention_game"),
    )

    conn.commit()

    cursor.close()
    conn.close()

@pytest.fixture
def mock_analytics_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    events = [
        # Level 1
        ("player_started_level", "test_player_001", "pytest_analytics_game",
         "2026-09-01T12:00:00", 1),
        ("level_completed", "test_player_001", "pytest_analytics_game",
         "2026-09-01T12:08:00", 1),

        ("player_started_level", "test_player_002", "pytest_analytics_game",
         "2026-09-01T13:00:00", 1),
        ("level_completed", "test_player_002", "pytest_analytics_game",
         "2026-09-01T13:07:00", 1),

        # Level 2
        ("player_started_level", "test_player_001", "pytest_analytics_game",
         "2026-09-01T12:20:00", 2),
        ("player_died", "test_player_001", "pytest_analytics_game",
         "2026-09-01T12:25:00", 2),
        ("level_completed", "test_player_001", "pytest_analytics_game",
         "2026-09-01T12:30:00", 2),

        ("player_started_level", "test_player_002", "pytest_analytics_game",
         "2026-09-01T13:20:00", 2),
        ("level_completed", "test_player_002", "pytest_analytics_game",
         "2026-09-01T13:30:00", 2),
    ]

    cursor.executemany(
        """
        INSERT INTO events (
            event,
            player_id,
            game_id,
            timestamp,
            level
        )
        VALUES (%s, %s, %s, %s, %s);
        """,
        events,
    )

    conn.commit()

    cursor.close()
    conn.close()

    yield

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM events WHERE game_id = %s;",
        ("pytest_analytics_game",)
    )

    conn.commit()

    cursor.close()
    conn.close()

@pytest.fixture
def session_test_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    events = [
        (
            "player_started_level",
            "session_test_player",
            "pytest_session_game",
            "2026-09-01T10:00:00",
            1,
        ),
        (
            "enemy_killed",
            "session_test_player",
            "pytest_session_game",
            "2026-09-01T10:10:00",
            1,
        ),
        (
            "player_died",
            "session_test_player",
            "pytest_session_game",
            "2026-09-01T10:20:00",
            1,
        ),

        # 40-minute gap → new session
        (
            "player_started_level",
            "session_test_player",
            "pytest_session_game",
            "2026-09-01T11:00:00",
            2,
        ),
        (
            "level_completed",
            "session_test_player",
            "pytest_session_game",
            "2026-09-01T11:05:00",
            2,
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO events (
            event,
            player_id,
            game_id,
            timestamp,
            level
        )
        VALUES (%s, %s, %s, %s, %s);
        """,
        events,
    )

    conn.commit()

    cursor.close()
    conn.close()

    yield

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM events WHERE game_id = %s;",
        ("pytest_session_game",)
    )

    conn.commit()

    cursor.close()
    conn.close()

@pytest.fixture
def retention_test_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    events = [
        # Day 0 — active players
        (
            "player_started_level",
            "retention_player_001",
            "pytest_retention_game",
            "2026-09-01T10:00:00",
            1,
        ),
        (
            "player_started_level",
            "retention_player_002",
            "pytest_retention_game",
            "2026-09-01T11:00:00",
            1,
        ),
        (
            "player_started_level",
            "retention_player_003",
            "pytest_retention_game",
            "2026-09-01T12:00:00",
            1,
        ),
        (
            "player_started_level",
            "retention_player_004",
            "pytest_retention_game",
            "2026-09-01T13:00:00",
            1,
        ),

        # Day 1 — players 001 and 002 return
        (
            "player_started_level",
            "retention_player_001",
            "pytest_retention_game",
            "2026-09-02T10:00:00",
            1,
        ),
        (
            "player_started_level",
            "retention_player_002",
            "pytest_retention_game",
            "2026-09-02T11:00:00",
            1,
        ),

        # Player 003 does not return
        # Player 004 does not return
    ]

    cursor.executemany(
        """
        INSERT INTO events (
            event,
            player_id,
            game_id,
            timestamp,
            level
        )
        VALUES (%s, %s, %s, %s, %s);
        """,
        events,
    )

    conn.commit()

    cursor.close()
    conn.close()

    yield

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM events WHERE game_id = %s;",
        ("pytest_retention_game",)
    )

    conn.commit()

    cursor.close()
    conn.close()