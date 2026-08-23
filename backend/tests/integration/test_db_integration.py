import uuid
import pytest
from database import get_db_connection


TEST_GAME_ID = f"db_test_game_{uuid.uuid4()}"
TEST_PLAYER_ID = f"db_test_player_{uuid.uuid4()}"


def test_postgres_connection_and_query():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    assert cursor.fetchone()[0] == 1
    cursor.close()
    conn.close()


def test_write_and_read_event():
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        event_data = {
            "event": "db_test",
            "player_id": TEST_PLAYER_ID,
            "game_id": TEST_GAME_ID,
            "timestamp": "2026-08-23T22:00:00",
            "level": 1,
        }

        cursor.execute(
            """
            INSERT INTO events (event, player_id, game_id, timestamp, level)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                event_data["event"],
                event_data["player_id"],
                event_data["game_id"],
                event_data["timestamp"],
                event_data["level"],
            ),
        )

        conn.commit()

        cursor.execute(
            """
            SELECT event, player_id, game_id, level
            FROM events
            WHERE game_id = %s
            """,
            (TEST_GAME_ID,),
        )

        row = cursor.fetchone()

        assert row is not None
        assert row[0] == "db_test"
        assert row[1] == TEST_PLAYER_ID
        assert row[2] == TEST_GAME_ID
        assert row[3] == 1

    finally:
        cursor.execute("DELETE FROM events WHERE game_id = %s", (TEST_GAME_ID,))
        conn.commit()
        cursor.close()
        conn.close()