import time
import uuid
from unittest.mock import patch

from database import get_db_connection
from redis_client import redis_client
from worker import recover_pending_messages


TEST_STREAM = f"questmetrix:test-recovery:{uuid.uuid4()}"
TEST_GROUP = "recovery-test-group"
TEST_CONSUMER = "dead-worker"

TEST_GAME_ID = f"recovery_test_game_{uuid.uuid4()}"
TEST_PLAYER_ID = f"recovery_test_player_{uuid.uuid4()}"


def test_pending_event_is_recovered():
    event_data = {
        "event": "recovery_test",
        "player_id": TEST_PLAYER_ID,
        "game_id": TEST_GAME_ID,
        "timestamp": "2026-08-23T22:00:00",
        "level": "1",
    }

    try:
        redis_client.xadd(
            TEST_STREAM,
            event_data,
        )

        redis_client.xgroup_create(
            TEST_STREAM,
            TEST_GROUP,
            id="0",
            mkstream=False,
        )

        redis_client.xreadgroup(
            groupname=TEST_GROUP,
            consumername=TEST_CONSUMER,
            streams={TEST_STREAM: ">"},
            count=1,
        )

        time.sleep(6)

        with patch("worker.STREAM_NAME", TEST_STREAM), \
             patch("worker.CONSUMER_GROUP", TEST_GROUP), \
             patch("worker.CONSUMER_NAME", "recovery-worker"):

            recover_pending_messages()

        conn = get_db_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT event, player_id, game_id, level
                FROM events
                WHERE game_id = %s
                """,
                (TEST_GAME_ID,),
            )

            row = cursor.fetchone()

        finally:
            cursor.close()
            conn.close()

        assert row is not None
        assert row[0] == "recovery_test"
        assert row[1] == TEST_PLAYER_ID
        assert row[2] == TEST_GAME_ID
        assert row[3] == 1

        pending = redis_client.xpending(
            TEST_STREAM,
            TEST_GROUP,
        )

        assert pending["pending"] == 0

    finally:
        redis_client.delete(TEST_STREAM)

        conn = get_db_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM events
                WHERE game_id = %s
                """,
                (TEST_GAME_ID,),
            )

            conn.commit()

        finally:
            cursor.close()
            conn.close()