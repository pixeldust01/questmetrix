from fastapi import Header, HTTPException
from database import get_db_connection

def verify_api_key(
    game_id: str,
    x_api_key: str | None,
):
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
        )

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM game_api_keys
            WHERE game_id = %s
              AND api_key = %s
            """,
            (game_id, x_api_key),
        )

        result = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )