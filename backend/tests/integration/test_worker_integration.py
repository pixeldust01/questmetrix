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
            # {k: v.encode("utf-8") for k, v in event_data.items()},
            event_data
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


def test_worker_processes_multiple_events():
    """
    Tests that the worker can successfully process a batch of multiple events.
    """
    test_stream = f"questmetrix:test-batch:{uuid.uuid4()}"
    test_group = "batch-test-group"
    test_consumer = "batch-worker"
    test_game_id = f"batch_game_{uuid.uuid4()}"
    num_events = 5

    try:
        # 1. Set up the consumer group
        redis_client.xgroup_create(
            test_stream,
            test_group,
            id="0",
            mkstream=True,
        )

        # 2. Add multiple events to the stream
        for i in range(num_events):
            event_data = {
                "event": "batch_test",
                "player_id": f"batch_player_{i}",
                "game_id": test_game_id,
                "timestamp": "2026-08-24T10:00:00",
                "level": str(i + 1),
            }
            redis_client.xadd(
                test_stream,
                event_data
            )

        # 3. Process the batch of events
        with patch("worker.STREAM_NAME", test_stream), \
             patch("worker.CONSUMER_GROUP", test_group), \
             patch("worker.CONSUMER_NAME", test_consumer):

            process_single_batch()

        # 4. Assert all events were written to the database
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM events WHERE game_id = %s",
                (test_game_id,),
            )
            count = cursor.fetchone()[0]
            assert count == num_events
        finally:
            cursor.close()
            conn.close()

        # 5. Assert all messages were acknowledged
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
    """
    Tests that a pending event from a "dead" worker is recovered and
    processed by another worker.
    """
    # Use unique names to avoid test conflicts
    test_stream = f"questmetrix:test-recovery:{uuid.uuid4()}"
    test_group = "recovery-test-group"
    dead_consumer = "dead-worker"
    recovery_consumer = "recovery-worker"
    test_game_id = f"recovery_game_{uuid.uuid4()}"
    test_player_id = f"recovery_player_{uuid.uuid4()}"

    event_data = {
        "event": "recovery_test",
        "player_id": test_player_id,
        "game_id": test_game_id,
        "timestamp": "2026-08-23T22:00:00",
        "level": "1",
    }

    try:
        # 1. Simulate a "dead" worker leaving a pending message.
        #    - Create a group and add a message to the stream.
        redis_client.xgroup_create(test_stream, test_group, id="0", mkstream=True)
        redis_client.xadd(test_stream, event_data)

        #    - Have the "dead" consumer read the message but not acknowledge it.
        redis_client.xreadgroup(
            groupname=test_group,
            consumername=dead_consumer,
            streams={test_stream: ">"},
            count=1,
        )

        #    - Verify the message is now pending.
        pending_before = redis_client.xpending(test_stream, test_group)
        assert pending_before["pending"] == 1

        # 2. Wait for the message to be idle long enough to be claimed.
        #    The recovery logic is configured to claim messages idle for >5s.
        time.sleep(6)

        # 3. Run the recovery process from a new worker.
        with patch("worker.STREAM_NAME", test_stream), \
             patch("worker.CONSUMER_GROUP", test_group), \
             patch("worker.CONSUMER_NAME", recovery_consumer):

            recover_pending_messages()

        # 4. Assert the event was written to the database.
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT player_id, game_id FROM events WHERE game_id = %s",
                (test_game_id,),
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == test_player_id
            assert row[1] == test_game_id
        finally:
            cursor.close()
            conn.close()

        # 5. Assert the message is no longer pending.
        pending_after = redis_client.xpending(test_stream, test_group)
        assert pending_after["pending"] == 0

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
            event_data
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

def test_worker_handles_malformed_event():
    """
    Tests that the worker does not acknowledge a message that is malformed
    and causes a database error.
    """
    test_stream = f"questmetrix:test-malformed:{uuid.uuid4()}"
    test_group = "malformed-test-group"
    test_consumer = "malformed-worker"
    test_game_id = f"malformed_game_{uuid.uuid4()}"

    malformed_event_data = {
        "event": "malformed_event",
        "player_id": "player_1",
        "game_id": test_game_id,
        "timestamp": "not-a-real-timestamp",
        "level": "this-is-not-a-number",
    }

    try:
        # 1. Set up the consumer group and add the malformed event
        redis_client.xgroup_create(test_stream, test_group, id="0", mkstream=True)
        redis_client.xadd(test_stream, malformed_event_data)

        # 2. Process the event
        with patch("worker.STREAM_NAME", test_stream), \
             patch("worker.CONSUMER_GROUP", test_group), \
             patch("worker.CONSUMER_NAME", test_consumer):

            # This will raise an exception internally, which is caught
            process_single_batch()

        # 3. Assert that the message was NOT written to the database
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM events WHERE game_id = %s",
                (test_game_id,),
            )
            row = cursor.fetchone()
            assert row is None
        finally:
            cursor.close()
            conn.close()

        # 4. Assert that the message is still pending
        pending = redis_client.xpending(test_stream, test_group)
        assert pending["pending"] == 1

    finally:
        # 5. Cleanup
        redis_client.delete(test_stream)
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE game_id = %s", (test_game_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()