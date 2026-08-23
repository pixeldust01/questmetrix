from unittest.mock import patch
from event_queue import publish_event


@patch("event_queue.redis_client")
def test_publish_event(mock_redis):
    mock_redis.xadd.return_value = "1234567890-0"

    event = {
        "event": "enemy_killed",
        "player_id": "player_1",
        "game_id": "game_1",
        "level": 1,
        "timestamp": "2026-08-23T01:00:00",
    }

    message_id = publish_event(event)

    assert message_id == "1234567890-0"
    mock_redis.xadd.assert_called_once()