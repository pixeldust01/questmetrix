from database import get_db_connection
from redis_client import redis_client

def create_event(event):
    conn = get_db_connection()
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
        RETURNING id;
        """,
        (
            event.event,
            event.player_id,
            event.game_id,
            event.timestamp,
            event.level,
        ),
    )

    event_id = cursor.fetchone()[0]

    conn.commit()
    redis_client.delete("games:statistics")

    cursor.close()
    conn.close()

    return event_id

def get_all_events():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            event,
            player_id,
            game_id,
            timestamp,
            level
        FROM events
        ORDER BY timestamp;
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows

