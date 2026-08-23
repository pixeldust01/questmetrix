import pytest
import time
from unittest.mock import patch
from redis_client import redis_client
from database import get_db_connection
from worker import run_worker, STREAM_NAME, CONSUMER_GROUP

@pytest.fixture(scope="function")
def setup_test_database():
    """
    A fixture to set up the database with a known set of test data
    and clean it up after the tests are done.
    This is a function-scoped fixture, so it runs for each test.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE events RESTART IDENTITY;")
    conn.commit()
    yield
    cursor.execute("TRUNCATE TABLE events RESTART IDENTITY;")
    conn.commit()
    cursor.close()
    conn.close()

@pytest.fixture(scope="function")
def redis_client_fixture():
    """
    A fixture to clean up the Redis stream after a test.
    """
    # Clean up before the test
    if redis_client.exists(STREAM_NAME):
        redis_client.delete(STREAM_NAME)
    yield redis_client
    # Clean up after the test
    if redis_client.exists(STREAM_NAME):
        redis_client.delete(STREAM_NAME)


def test_worker_recovers_pending_event(setup_test_database, redis_client_fixture, monkeypatch):
    """
    Tests that the worker can recover a pending event that a previous worker failed to process.
    """
    # 1. Publish a test event to the stream
    event_data = {
        "event": "player_started_level",
        "player_id": "player_recovery_test",
        "game_id": "game_recovery_test",
        "timestamp": "2026-08-23T10:00:00Z",
        "level": "1",
    }
    message_id = redis_client_fixture.xadd(STREAM_NAME, event_data)
    assert message_id is not None

    # 2. Simulate a failure in store_event using monkeypatch.
    #    The first time the worker runs, it will fail to store the event.
    original_store_event = "worker.store_event"
    call_count = {"count": 0}
    def mock_store_event_fails_once(event_data):
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise Exception("Simulated database connection error!")
        # On the second call (recovery), the original function will be called
        with patch(original_store_event) as mock_original:
            return mock_original(event_data)

    monkeypatch.setattr(original_store_event, mock_store_event_fails_once)

    # 3. Run the worker once. It will process the message, fail, and create a pending entry.
    run_worker(run_once=True)

    # 4. Verify that the event is now in the pending state.
    pending_summary = redis_client_fixture.xpending(STREAM_NAME, CONSUMER_GROUP)
    assert pending_summary["pending"] == 1, "Event should be in pending state"

    # Give it a moment to ensure the message is considered "idle"
    time.sleep(1.5)

    # 5. Run the worker again. This time, it should recover and process the pending event.
    #    We remove the patch so the real store_event is called during recovery.
    monkeypatch.undo()
    run_worker(run_once=True)

    # 6. Verify the outcome
    # Check that the event is no longer pending
    pending_summary_after_recovery = redis_client_fixture.xpending(STREAM_NAME, CONSUMER_GROUP)
    assert pending_summary_after_recovery["pending"] == 0, "Event should be processed and no longer pending"

    # Check that the event was successfully saved to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM events WHERE player_id = 'player_recovery_test';")
    count = cursor.fetchone()[0]
    assert count == 1, "Event should be saved to the database after recovery"
    cursor.close()
    conn.close()