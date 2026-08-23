from redis_client import redis_client

STREAM_NAME = "questmetrix:events"

def publish_event(event: dict):
    event_data = {
        key: str(value)
        for key, value in event.items()
    }

    return redis_client.xadd(
        STREAM_NAME,
        event_data,
    )