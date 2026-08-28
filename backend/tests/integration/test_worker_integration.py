import time
import uuid
from unittest.mock import patch
from database import get_db_connection
from redis_client import redis_client
from worker import recover_pending_messages, process_single_batch


TEST_STREAM = f"questmetrix:test-recovery:{uuid.uuid4()}"
TEST_GROUP = "recovery-test-group"
TEST_CONSUMER = "dead-worker"

TEST_GAME_ID = f"recovery_test_game_{uuid.uuid4()}"
TEST_PLAYER_ID = f"recovery_test_player_{uuid.uuid4()}"


def test_worker_processes_event():
    """
    Tests the normal, successful processing of a single event by the worker.
    """
    test_stream = f"questmetrix:test-normal:{uuid.uuid4()}"
    test_group = "normal-test-group"
    test_consumer = "normal-worker"
    test_game_id = f"normal_game_{uuid.uuid4()}"
    test_player_id = f"normal_player_{uuid.uuid4()}"

    event_data = {
        "event": "normal_test",
        "player_id": test_player_id,
        "game_id": test_game_id,
        "timestamp": "2026-08-23T22:00:00",
        "level": "1",
    }

    try:
        # 1. Set up the consumer group
        redis_client.xgroup_create(
            test_stream,
            test_group,
            id="0",
            mkstream=True,
        )

        # 2. Add an event to the stream
        redis_client.xadd(
            test_stream,
            {k: v.encode("utf-8") for k, v in event_data.items()},
        )

        # 3. Process the event
        with patch("worker.STREAM_NAME", test_stream), \
             patch("worker.CONSUMER_GROUP", test_group), \
             patch("worker.CONSUMER_NAME", test_consumer):

            process_single_batch()

        # 4. Assert the event was written to the database
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM events WHERE game_id = %s",
                (test_game_id,),
            )
            row = cursor.fetchone()
            assert row is not None
        finally:
            cursor.close()
            conn.close()

        # 5. Assert the message was acknowledged
        pending = redis_client.xpending(test_stream, test_group)
        assert pending["pending"] == 0

    finally:
        # 6. Cleanup
        redis_client.delete(test_stream)
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE game_id = %s", (test_game_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


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
            {k: v.encode("utf-8") for k, v in event_data.items()},
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


def test_pending_event_recovery_fails_on_db_error():
    """
    Tests that a pending message is not acknowledged if storing it in the
    database fails during recovery.
    """
    # Use unique names to avoid test conflicts
    test_stream = f"questmetrix:test-recovery-fail:{uuid.uuid4()}"
    test_group = "recovery-fail-group"
    test_consumer = "dead-worker-fail"
    test_game_id = f"recovery_fail_game_{uuid.uuid4()}"
    test_player_id = f"recovery_fail_player_{uuid.uuid4()}"

    event_data = {
        "event": "recovery_fail_test",
        "player_id": test_player_id,
        "game_id": test_game_id,
        "timestamp": "2026-08-23T22:00:00",
        "level": "1",
    }

    try:
        # 1. Create a pending message
        redis_client.xadd(
            test_stream,
            {k: v.encode("utf-8") for k, v in event_data.items()},
        )
        redis_client.xgroup_create(
            test_stream,
            test_group,
            id="0",
            mkstream=False,
        )
        redis_client.xreadgroup(
            groupname=test_group,
            consumername=test_consumer,
            streams={test_stream: ">"},
            count=1,
        )

        # Wait for the message to be idle long enough to be claimed
        time.sleep(6)

        # 2. Mock the database insertion to fail
        with patch("worker.store_event", side_effect=Exception("DB error")), \
             patch("worker.STREAM_NAME", test_stream), \
             patch("worker.CONSUMER_GROUP", test_group), \
             patch("worker.CONSUMER_NAME", "recovery-worker-fail"):

            # 3. Attempt recovery
            recover_pending_messages()

        # 4. Assert message is still pending
        pending = redis_client.xpending(
            test_stream,
            test_group,
        )
        assert pending["pending"] == 1

        # 5. Assert message was NOT written to DB
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM events WHERE game_id = %s", (test_game_id,))
            row = cursor.fetchone()
            assert row is None
        finally:
            cursor.close()
            conn.close()

    finally:
        redis_client.delete(test_stream)
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE game_id = %s", (test_game_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()