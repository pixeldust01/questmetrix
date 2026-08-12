from database import get_db_connection

def get_level_statistics(game_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            started.level,

            started.players_started,

            COALESCE(completed.players_completed, 0)
                AS players_completed,

            ROUND(
                COALESCE(completed.players_completed, 0) * 100.0
                / NULLIF(started.players_started, 0),
                2
            ) AS completion_rate,

            COALESCE(deaths.total_deaths, 0)
                AS total_deaths,

            COALESCE(deaths.players_died, 0)
                AS players_died,

            ROUND(
                COALESCE(deaths.total_deaths, 0) * 1.0
                / NULLIF(started.players_started, 0),
                2
            ) AS average_deaths,

            ROUND(
                completion_times.average_completion_time_seconds,
                2
            ) AS average_completion_time_seconds

        FROM
        (
            SELECT
                level,
                COUNT(DISTINCT player_id) AS players_started
            FROM events
            WHERE game_id = %s
              AND event = 'player_started_level'
            GROUP BY level
        ) AS started

        LEFT JOIN
        (
            SELECT
                level,
                COUNT(DISTINCT player_id) AS players_completed
            FROM events
            WHERE game_id = %s
              AND event = 'level_completed'
            GROUP BY level
        ) AS completed
            ON started.level = completed.level

        LEFT JOIN
        (
            SELECT
                level,
                COUNT(*) AS total_deaths,
                COUNT(DISTINCT player_id) AS players_died
            FROM events
            WHERE game_id = %s
              AND event = 'player_died'
            GROUP BY level
        ) AS deaths
            ON started.level = deaths.level

        LEFT JOIN
        (
            SELECT
                level,
                AVG(completion_time_seconds)
                    AS average_completion_time_seconds
            FROM
            (
                SELECT
                    started_events.player_id,
                    started_events.level,

                    EXTRACT(
                        EPOCH FROM (
                            completed_events.timestamp
                            - started_events.timestamp
                        )
                    ) AS completion_time_seconds

                FROM events AS started_events

                JOIN events AS completed_events
                    ON started_events.player_id = completed_events.player_id
                    AND started_events.game_id = completed_events.game_id
                    AND started_events.level = completed_events.level

                WHERE started_events.game_id = %s
                  AND started_events.event = 'player_started_level'
                  AND completed_events.event = 'level_completed'
            ) AS completion_times

            GROUP BY level
        ) AS completion_times
            ON started.level = completion_times.level

        ORDER BY started.level;
        """,
        (game_id, game_id, game_id, game_id),
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "level": row[0],
            "players_started": row[1],
            "players_completed": row[2],
            "completion_rate": float(row[3]),
            "total_deaths": row[4],
            "players_died": row[5],
            "average_deaths": float(row[6]),
            "average_completion_time_seconds": (
                float(row[7])
                if row[7] is not None
                else None
            ),
        }
        for row in rows
    ]

def get_game_statistics():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            game_id,
            COUNT(*) AS event_count
        FROM events
        GROUP BY game_id
        ORDER BY game_id;
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "game_id": row[0],
            "event_count": row[1]
        }
        for row in rows
    ]

def get_player_statistics():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            player_id,
            COUNT(*) AS event_count
        FROM events
        GROUP BY player_id
        ORDER BY player_id;
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "player_id": row[0],
            "event_count": row[1]
        }
        for row in rows
    ]

