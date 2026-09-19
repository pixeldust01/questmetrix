import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from worker import process_single_batch


def test_worker_broadcasts_after_successful_processing():
    event_data = {
        "event": "enemy_killed",
        "player_id": "player_1",
        "game_id": "game_1",
        "timestamp": "2026-08-23T01:00:00",
        "level": "1",
    }
    redis = MagicMock()
    redis.xreadgroup.return_value = [
        ("questmetrix:events", [("1-0", event_data)])
    ]
    manager = MagicMock()
    manager.broadcast = AsyncMock()

    with patch("worker.redis_client", redis), \
         patch("worker.manager", manager), \
         patch("worker.store_event") as store_event:
        asyncio.run(process_single_batch())

    store_event.assert_called_once_with(event_data)
    redis.xack.assert_called_once_with(
        "questmetrix:events",
        "questmetrix-workers",
        "1-0",
    )
    manager.broadcast.assert_awaited_once_with(event_data)


def test_worker_does_not_broadcast_when_processing_fails():
    event_data = {
        "event": "enemy_killed",
        "player_id": "player_1",
        "game_id": "game_1",
        "timestamp": "2026-08-23T01:00:00",
        "level": "1",
    }
    redis = MagicMock()
    redis.xreadgroup.return_value = [
        ("questmetrix:events", [("1-0", event_data)])
    ]
    manager = MagicMock()
    manager.broadcast = AsyncMock()

    with patch("worker.redis_client", redis), \
         patch("worker.manager", manager), \
         patch("worker.store_event", side_effect=Exception("DB error")):
        asyncio.run(process_single_batch())

    redis.xack.assert_not_called()
    manager.broadcast.assert_not_awaited()