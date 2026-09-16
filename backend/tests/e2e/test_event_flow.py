import uuid
import time
import os
import requests
from database import get_db_connection


BASE_URL = os.environ.get("BASE_URL", "http://backend:8000")


def setup_api_key(game_id, api_key):
    """Inserts an API key into the database for a test."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO game_api_keys (game_id, api_key) VALUES (%s, %s)",
            (game_id, api_key),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def cleanup_db(game_id):
    """Removes test data from the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE game_id = %s", (game_id,))
        cursor.execute("DELETE FROM game_api_keys WHERE game_id = %s", (game_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def test_event_persists_to_database():
    game_id = f"e2e_game_{uuid.uuid4()}"
    player_id = f"e2e_player_{uuid.uuid4()}"
    api_key = f"e2e_key_{uuid.uuid4()}"
    headers = {"X-API-Key": api_key}

    setup_api_key(game_id, api_key)

    try:
        # 1. Post real event to API
        event = {
            "event": "e2e_test",
            "player_id": player_id,
            "game_id": game_id,
            "timestamp": "2026-01-01T00:00:00",
            "level": 1,
        }
        response = requests.post(f"{BASE_URL}/events", json=event, headers=headers)
        assert response.status_code == 200

        # 2. Poll the database to verify persistence
        max_wait_time = 15
        start_time = time.time()
        results = []
        while time.time() - start_time < max_wait_time:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT player_id, game_id FROM events WHERE game_id = %s", (game_id,)
            )
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            if results:
                break
            time.sleep(0.5)

        # 3. Assert that the event was found
        assert len(results) > 0, "Event was not persisted to the database"
        assert results[0][0] == player_id
        assert results[0][1] == game_id

    finally:
        cleanup_db(game_id)


def test_queue_event_api_responds_correctly():
    game_id = f"e2e_game_{uuid.uuid4()}"
    api_key = f"e2e_key_{uuid.uuid4()}"
    headers = {"X-API-Key": api_key}
    event_data = {
        "event": "e2e_test_queue",
        "player_id": f"e2e_player_{uuid.uuid4()}",
        "game_id": game_id,
        "timestamp": "2026-01-01T00:00:00",
        "level": 1,
    }

    setup_api_key(game_id, api_key)

    try:
        # 1. Post event and check API response
        response = requests.post(f"{BASE_URL}/events", json=event_data, headers=headers)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["message"] == "Event queued successfully!"
        assert "message_id" in response_data
        assert response_data["event"] == event_data

        # 2. Poll the database to verify persistence
        max_wait_time = 15
        start_time = time.time()
        results = []
        while time.time() - start_time < max_wait_time:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT player_id, game_id FROM events WHERE game_id = %s", (game_id,)
            )
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            if results:
                break
            time.sleep(0.5)

        # 3. Assert that the event was found and is correct
        assert len(results) > 0, "Worker did not persist queued event"
        assert results[0][0] == event_data["player_id"]
        assert results[0][1] == game_id

    finally:
        cleanup_db(game_id)


def test_e2e_analytics_after_ingestion():
    game_id = f"e2e_analytics_game_{uuid.uuid4()}"
    api_key = f"e2e_key_{uuid.uuid4()}"
    headers = {"X-API-Key": api_key}
    player_1 = f"e2e_analytics_player_1_{uuid.uuid4()}"
    player_2 = f"e2e_analytics_player_2_{uuid.uuid4()}"

    events_to_post = [
        {"event": "player_started_level", "player_id": player_1, "game_id": game_id, "timestamp": "2026-08-28T10:00:00", "level": 1},
        {"event": "level_completed", "player_id": player_1, "game_id": game_id, "timestamp": "2026-08-28T10:05:00", "level": 1},
        {"event": "player_started_level", "player_id": player_2, "game_id": game_id, "timestamp": "2026-08-28T11:00:00", "level": 1},
        {"event": "player_died", "player_id": player_2, "game_id": game_id, "timestamp": "2026-08-28T11:01:00", "level": 1},
        {"event": "player_started_level", "player_id": player_1, "game_id": game_id, "timestamp": "2026-08-28T10:10:00", "level": 2},
    ]

    setup_api_key(game_id, api_key)

    try:
        # 1. Post all events
        for event in events_to_post:
            response = requests.post(f"{BASE_URL}/events", json=event, headers=headers)
            assert response.status_code == 200

        # 2. Poll for persistence
        for _ in range(10):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events WHERE game_id = %s", (game_id,))
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            if count == len(events_to_post):
                break
            time.sleep(1)
        else:
            assert False, "Worker did not process events in time"

        # 3. Query analytics
        response = requests.get(f"{BASE_URL}/levels?game_id={game_id}")
        assert response.status_code == 200
        analytics_data = response.json()

        # 4. Verify analytics
        expected_data = [
            {"level": 1, "players_started": 2, "players_completed": 1, "completion_rate": 50.0, "total_deaths": 1, "players_died": 1, "average_deaths": 0.5, "average_completion_time_seconds": 300.0},
            {"level": 2, "players_started": 1, "players_completed": 0, "completion_rate": 0.0, "total_deaths": 0, "players_died": 0, "average_deaths": 0.0, "average_completion_time_seconds": None},
        ]
        sorted_analytics = sorted(analytics_data, key=lambda x: x['level'])
        assert sorted_analytics == expected_data

    finally:
        cleanup_db(game_id)


def test_e2e_validation_failure_missing_field():
    game_id = f"e2e_validation_game_{uuid.uuid4()}"
    api_key = f"e2e_key_{uuid.uuid4()}"
    headers = {"X-API-Key": api_key}
    malformed_event = {"event": "bad_event", "player_id": "player_1", "game_id": game_id, "level": 1}

    setup_api_key(game_id, api_key)

    try:
        response = requests.post(f"{BASE_URL}/events", json=malformed_event, headers=headers)
        assert response.status_code == 422

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM events WHERE game_id = %s", (game_id,))
        assert cursor.fetchone() is None
        cursor.close()
        conn.close()
    finally:
        cleanup_db(game_id)


def test_e2e_validation_failure_invalid_value():
    game_id = f"e2e_validation_game_{uuid.uuid4()}"
    api_key = f"e2e_key_{uuid.uuid4()}"
    headers = {"X-API-Key": api_key}
    malformed_event = {"event": "bad_event", "player_id": "player_1", "game_id": game_id, "timestamp": "not-a-timestamp", "level": 1}

    setup_api_key(game_id, api_key)

    try:
        response = requests.post(f"{BASE_URL}/events", json=malformed_event, headers=headers)
        assert response.status_code == 422

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM events WHERE game_id = %s", (game_id,))
        assert cursor.fetchone() is None
        cursor.close()
        conn.close()
    finally:
        cleanup_db(game_id)


def test_auth_failure_missing_key():
    event = {"event": "e2e_test", "player_id": "p1", "game_id": "g1", "timestamp": "2026-01-01T00:00:00", "level": 1}
    response = requests.post(f"{BASE_URL}/events", json=event)
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API key"


def test_auth_failure_invalid_key():
    headers = {"X-API-Key": "invalid_key"}
    event = {"event": "e2e_test", "player_id": "p1", "game_id": "g1", "timestamp": "2026-01-01T00:00:00", "level": 1}
    response = requests.post(f"{BASE_URL}/events", json=event, headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"


def test_auth_failure_wrong_game_for_key():
    game_id_1 = f"e2e_game_{uuid.uuid4()}"
    game_id_2 = f"e2e_game_{uuid.uuid4()}"
    api_key_1 = f"e2e_key_{uuid.uuid4()}"
    headers = {"X-API-Key": api_key_1}

    setup_api_key(game_id_1, api_key_1)

    try:
        event = {"event": "e2e_test", "player_id": "p1", "game_id": game_id_2, "timestamp": "2026-01-01T00:00:00", "level": 1}
        response = requests.post(f"{BASE_URL}/events", json=event, headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid API key"
    finally:
        cleanup_db(game_id_1)