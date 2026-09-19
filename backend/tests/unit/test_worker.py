import asyncio
import json
from unittest.mock import MagicMock, patch

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

    with patch("worker.redis_client", redis), \
         patch("worker.store_event") as store_event:
        asyncio.run(process_single_batch())

    store_event.assert_called_once_with(event_data)
    redis.xack.assert_called_once_with(
        "questmetrix:events",
        "questmetrix-workers",
        "1-0",
    )
    published_event = json.loads(
        redis.publish.call_args.args[1]
    )
    assert published_event == {
        **event_data,
        "level": 1,
    }


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

    with patch("worker.redis_client", redis), \
         patch("worker.store_event", side_effect=Exception("DB error")):
        asyncio.run(process_single_batch())

    redis.xack.assert_not_called()
    redis.publish.assert_not_called()