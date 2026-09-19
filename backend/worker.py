import logging
import asyncio
from redis.exceptions import ResponseError
from redis_client import redis_client
from database import get_db_connection
from websocket_manager import manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


STREAM_NAME = "questmetrix:events"
CONSUMER_GROUP = "questmetrix-workers"
CONSUMER_NAME = "worker-1"

def ensure_consumer_group():
    try:
        redis_client.xgroup_create(
            name=STREAM_NAME,
            groupname=CONSUMER_GROUP,
            id="0",
            mkstream=True,
        )

        logging.info(
            f"Created Redis consumer group '{CONSUMER_GROUP}'."
        )

    except ResponseError as error:
        if "BUSYGROUP" in str(error):
            logging.info(
                f"Redis consumer group '{CONSUMER_GROUP}' already exists."
            )
        else:
            raise

def store_event(event_data):
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO events (
                event,
                player_id,
                game_id,
                timestamp,
                level
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                event_data["event"],
                event_data["player_id"],
                event_data["game_id"],
                event_data["timestamp"],
                int(event_data["level"]),
            ),
        )

        conn.commit()

    finally:
        cursor.close()
        conn.close()

async def run_worker():
    ensure_consumer_group()

    logging.info("QuestMetrix worker started.")

    await recover_pending_messages()

    while True:
        await process_single_batch()


async def process_single_batch():
    messages = redis_client.xreadgroup(
        groupname=CONSUMER_GROUP,
        consumername=CONSUMER_NAME,
        streams={STREAM_NAME: ">"},
        count=10,
        block=1000,
    )

    if not messages:
        return

    for _, stream_messages in messages:
        for message_id, event_data in stream_messages:
            try:
                store_event(event_data)

                redis_client.xack(
                    STREAM_NAME,
                    CONSUMER_GROUP,
                    message_id,
                )

                logging.info(f"Processed event {message_id}")

                await manager.broadcast(event_data)

            except Exception as error:
                logging.error(
                    f"Failed to process event "
                    f"{message_id}: {error}"
                )

async def recover_pending_messages():
    try:
        result = redis_client.xautoclaim(
            STREAM_NAME,
            CONSUMER_GROUP,
            CONSUMER_NAME,
            min_idle_time=5000,
            start_id="0-0",
            count=10,
        )

        messages = result[1]

        for message_id, event_data in messages:

            try:
                store_event(event_data)

                redis_client.xack(
                    STREAM_NAME,
                    CONSUMER_GROUP,
                    message_id,
                )

                logging.info(
                    f"Recovered pending event {message_id}"
                )

                await manager.broadcast(event_data)

            except Exception as error:
                logging.error(
                    f"Failed to recover event "
                    f"{message_id}: {error}"
                )

    except Exception:
        logging.exception(
            "Failed to recover pending messages"
        )


if __name__ == "__main__":
    asyncio.run(run_worker())