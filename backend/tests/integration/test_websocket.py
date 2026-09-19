import asyncio
import json
import os
import pytest
import websockets
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
WS_URL = os.getenv("WS_URL", "ws://localhost:8000")

url = f"{WS_URL}/ws/events"

@pytest.mark.asyncio
async def test_websocket_receives_processed_event():
    async with websockets.connect(f"{WS_URL}/ws/events") as websocket:
        # Give the WebSocket connection a moment to register.
        await asyncio.sleep(0.2)

        event = {
            "event": "enemy_killed",
            "player_id": "websocket_test_player",
            "game_id": "mock_analytics_game",
            "timestamp": "2026-09-19T20:00:00",
            "level": 1,
        }

        response = requests.post(
            f"{BASE_URL}/events",
            json=event,
            headers={
                "X-API-Key": "qm_test_key_12345",
            },
        )

        assert response.status_code == 200

        # Wait for the worker → Redis Pub/Sub → WebSocket path.
        message = await asyncio.wait_for(
            websocket.recv(),
            timeout=10,
        )

        received_event = json.loads(message)

        assert received_event["event"] == "enemy_killed"
        assert received_event["player_id"] == "websocket_test_player"
        assert received_event["game_id"] == "mock_analytics_game"
        assert received_event["level"] == 1