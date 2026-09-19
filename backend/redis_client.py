import redis
import os

PUBSUB_CHANNEL = "questmetrix:processed_events"

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
    socket_timeout=10,
)