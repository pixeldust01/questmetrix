import uuid
import time
import os
import requests
from database import get_db_connection


BASE_URL = os.environ.get("BASE_URL", "http://backend:8000")

TEST_GAME_ID = f"e2e_game_{uuid.uuid4()}"
TEST_PLAYER_ID = f"e2e_player_{uuid.uuid4()}"


def test_event_persists_to_database():
    try:
        # 1. Post real event to API
        event = {
            "event": "e2e_test",
            "player_id": TEST_PLAYER_ID,
            "game_id": TEST_GAME_ID,
            "timestamp": "2026-01-01T00:00:00",
            "level": 1,
        }
        response = requests.post(f"{BASE_URL}/events", json=event)
        assert response.status_code == 200

        # 2. Poll the database to verify persistence
        max_wait_time = 15  # seconds
        start_time = time.time()
        results = []
        while time.time() - start_time < max_wait_time:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT player_id, game_id
                FROM events
                WHERE game_id = %s
                """,
                (TEST_GAME_ID,),
            )
            results = cursor.fetchall()
            cursor.close()
            conn.close()

            if results:
                break
            time.sleep(0.5)  # Wait 0.5 seconds before retrying

        # 3. Assert that the event was found
        assert len(results) > 0

        # More specific assertions
        assert results[0][0] == TEST_PLAYER_ID
        assert results[0][1] == TEST_GAME_ID

    finally:
        # 4. Clean up the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE game_id = %s", (TEST_GAME_ID,))
        conn.commit()
        cursor.close()
        conn.close()


def test_queue_event_api_responds_correctly():
    game_id = f"e2e_game_{uuid.uuid4()}"
    event_data = {
        "event": "e2e_test_queue",
        "player_id": f"e2e_player_{uuid.uuid4()}",
        "game_id": game_id,
        "timestamp": "2026-01-01T00:00:00",
        "level": 1,
    }
    try:
        # 1. Post event and check API response
        response = requests.post(f"{BASE_URL}/events", json=event_data)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["message"] == "Event queued successfully!"
        assert "message_id" in response_data
        assert response_data["event"] == event_data

        # 2. Poll the database to verify persistence
        max_wait_time = 15  # seconds
        start_time = time.time()
        results = []
        while time.time() - start_time < max_wait_time:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT player_id, game_id
                FROM events
                WHERE game_id = %s
                """,
                (game_id,),
            )
            results = cursor.fetchall()
            cursor.close()
            conn.close()

            if results:
                break
            time.sleep(0.5)  # Wait 0.5 seconds before retrying

        # 3. Assert that the event was found and is correct
        assert len(results) > 0, "Worker did not persist queued event"
        assert results[0][0] == event_data["player_id"]
        assert results[0][1] == game_id

    finally:
        # 4. Clean up the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE game_id = %s", (game_id,))
        conn.commit()
        cursor.close()
        conn.close()


def test_e2e_analytics_after_ingestion():
    """
    Tests the full E2E flow from event ingestion to analytics query.
    """
    game_id = f"e2e_analytics_game_{uuid.uuid4()}"
    player_1 = f"e2e_analytics_player_1_{uuid.uuid4()}"
    player_2 = f"e2e_analytics_player_2_{uuid.uuid4()}"

    events_to_post = [
        # Player 1 starts and completes level 1
        {
            "event": "player_started_level", "player_id": player_1, "game_id": game_id,
            "timestamp": "2026-08-28T10:00:00", "level": 1
        },
        {
            "event": "level_completed", "player_id": player_1, "game_id": game_id,
            "timestamp": "2026-08-28T10:05:00", "level": 1
        },
        # Player 2 starts level 1 and dies
        {
            "event": "player_started_level", "player_id": player_2, "game_id": game_id,
            "timestamp": "2026-08-28T11:00:00", "level": 1
        },
        {
            "event": "player_died", "player_id": player_2, "game_id": game_id,
            "timestamp": "2026-08-28T11:01:00", "level": 1
        },
        # Player 1 starts level 2
        {
            "event": "player_started_level", "player_id": player_1, "game_id": game_id,
            "timestamp": "2026-08-28T10:10:00", "level": 2
        },
    ]

    try:
        # 1. Post all events via the API
        for event in events_to_post:
            response = requests.post(f"{BASE_URL}/events", json=event)
            assert response.status_code == 200

        # 2. Poll the database to wait for the worker to process events
        for _ in range(10):  # Poll for up to 10 seconds
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM events WHERE game_id = %s", (game_id,))
                count = cursor.fetchone()[0]
                if count == len(events_to_post):
                    break
            finally:
                cursor.close()
                conn.close()
            time.sleep(1)
        else:
            assert False, "Worker did not process events in time"

        # 3. Query the analytics endpoint
        response = requests.get(f"{BASE_URL}/levels?game_id={game_id}")
        assert response.status_code == 200
        analytics_data = response.json()

        # 4. Verify the analytics response
        expected_data = [
            {
                "level": 1,
                "players_started": 2,
                "players_completed": 1,
                "completion_rate": 50.0,
                "total_deaths": 1,
                "players_died": 1,
                "average_deaths": 0.5,
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
        
        # Sort by level to ensure consistent order for comparison
        sorted_analytics = sorted(analytics_data, key=lambda x: x['level'])
        
        assert sorted_analytics == expected_data

    finally:
        # 5. Cleanup
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE game_id = %s", (game_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


def test_e2e_validation_failure_missing_field():
    """
    Tests that the API correctly rejects an event with a missing field.
    """
    game_id = f"e2e_validation_game_{uuid.uuid4()}"

    # Malformed: 'timestamp' field is missing
    malformed_event = {
        "event": "bad_event",
        "player_id": "player_1",
        "game_id": game_id,
        "level": 1,
    }

    # 1. Post the malformed event
    response = requests.post(f"{BASE_URL}/events", json=malformed_event)

    # 2. Assert that the request was rejected
    assert response.status_code == 422

    # 3. Assert that nothing was written to the database
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM events WHERE game_id = %s", (game_id,))
        row = cursor.fetchone()
        assert row is None
    finally:
        cursor.close()
        conn.close()


def test_e2e_validation_failure_invalid_value():
    """
    Tests that the API correctly rejects an event with a malformed value.
    """
    game_id = f"e2e_validation_game_{uuid.uuid4()}"

    # Malformed: 'timestamp' is not a valid ISO 8601 timestamp
    malformed_event = {
        "event": "bad_event",
        "player_id": "player_1",
        "game_id": game_id,
        "timestamp": "not-a-timestamp",
        "level": 1,
    }

    # 1. Post the malformed event
    response = requests.post(f"{BASE_URL}/events", json=malformed_event)

    # 2. Assert that the request was rejected
    assert response.status_code == 422

    # 3. Assert that nothing was written to the database
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM events WHERE game_id = %s", (game_id,))
        row = cursor.fetchone()
        assert row is None
    finally:
        cursor.close()
        conn.close()