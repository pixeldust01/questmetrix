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

def get_sessions(game_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        WITH ordered_events AS (
            SELECT
                player_id,
                game_id,
                timestamp,
                event,
                level,

                LAG(timestamp) OVER (
                    PARTITION BY player_id, game_id
                    ORDER BY timestamp
                ) AS previous_timestamp

            FROM events

            WHERE game_id = %s
        ),

        session_markers AS (
            SELECT
                *,
                CASE
                    WHEN previous_timestamp IS NULL THEN 1
                    WHEN timestamp - previous_timestamp
                         > INTERVAL '30 minutes'
                    THEN 1
                    ELSE 0
                END AS new_session

            FROM ordered_events
        ),

        session_numbers AS (
            SELECT
                *,
                SUM(new_session) OVER (
                    PARTITION BY player_id, game_id
                    ORDER BY timestamp
                ) AS session_number

            FROM session_markers
        )

        SELECT
            player_id,
            game_id,
            session_number,
            MIN(timestamp) AS session_start,
            MAX(timestamp) AS session_end,
            COUNT(*) AS event_count

        FROM session_numbers

        GROUP BY
            player_id,
            game_id,
            session_number

        ORDER BY
            player_id,
            session_number;
        """,
        (game_id,),
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "player_id": row[0],
            "game_id": row[1],
            "session_number": row[2],
            "session_start": row[3],
            "session_end": row[4],
            "event_count": row[5],
        }
        for row in rows
    ]

def get_retention(game_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        WITH daily_players AS (
            SELECT DISTINCT
                player_id,
                DATE(timestamp) AS activity_date
            FROM events
            WHERE game_id = %s
        ),

        day_zero AS (
            SELECT
                player_id,
                activity_date AS cohort_date
            FROM daily_players
        ),

        retained_players AS (
            SELECT DISTINCT
                d0.player_id,
                d0.cohort_date
            FROM day_zero d0

            JOIN daily_players d1
                ON d0.player_id = d1.player_id
                AND d1.activity_date =
                    d0.cohort_date + INTERVAL '1 day'
        )

        SELECT
            d0.cohort_date,
            COUNT(DISTINCT d0.player_id),
            COUNT(DISTINCT r.player_id),
            ROUND(
                COUNT(DISTINCT r.player_id) * 100.0
                / NULLIF(COUNT(DISTINCT d0.player_id), 0),
                2
            )
        FROM day_zero d0

        LEFT JOIN retained_players r
            ON d0.player_id = r.player_id
            AND d0.cohort_date = r.cohort_date

        GROUP BY d0.cohort_date
        ORDER BY d0.cohort_date;
        """,
        (game_id,),
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "cohort_date": row[0],
            "players_active": row[1],
            "players_returned": row[2],
            "day_1_retention": float(row[3]),
        }
        for row in rows
    ]