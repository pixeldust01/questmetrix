import asyncio
import json

from redis_client import redis_client, PUBSUB_CHANNEL
from websocket_manager import manager


async def listen_for_processed_events():
    pubsub = redis_client.pubsub()
    pubsub.subscribe(PUBSUB_CHANNEL)

    while True:
        try:
            message = pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if message and message["type"] == "message":
                event_data = json.loads(message["data"])
                event_data["level"] = int(event_data["level"])

                await manager.broadcast(event_data)

            await asyncio.sleep(0.01)

        except Exception as error:
            print(f"Redis Pub/Sub listener error: {error}")
            await asyncio.sleep(1)