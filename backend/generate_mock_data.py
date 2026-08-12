from datetime import datetime, timedelta
from database import get_db_connection

GAME_ID = "mock_analytics_game"

def add_event(events, event_name, player_id, timestamp, level):
    events.append(
        (
            event_name,
            player_id,
            GAME_ID,
            timestamp,
            level,
        )
    )


def generate_player_events(player_id, start_time, level_data):
    events = []
    current_time = start_time

    for level, data in level_data.items():
        completed = data["completed"]
        deaths = data["deaths"]
        duration_minutes = data["duration_minutes"]

        level_start = current_time

        # Player starts the level
        add_event(
            events,
            "player_started_level",
            player_id,
            level_start,
            level,
        )

        # Some normal gameplay
        add_event(
            events,
            "enemy_killed",
            player_id,
            level_start + timedelta(minutes=1),
            level,
        )

        add_event(
            events,
            "item_collected",
            player_id,
            level_start + timedelta(minutes=2),
            level,
        )

        # Deaths, if any
        for death_number in range(deaths):
            death_time = level_start + timedelta(
                minutes=3 + death_number
            )

            add_event(
                events,
                "player_died",
                player_id,
                death_time,
                level,
            )

        # Level outcome
        end_time = level_start + timedelta(
            minutes=duration_minutes
        )

        if completed:
            add_event(
                events,
                "level_completed",
                player_id,
                end_time,
                level,
            )
        else:
            add_event(
                events,
                "player_quit",
                player_id,
                end_time,
                level,
            )

        # Leave some time before the next level
        current_time = end_time + timedelta(minutes=10)

    return events


def main():
    all_events = []

    base_time = datetime(2026, 9, 1, 12, 0, 0)

    players = {
        "player_001": {
            1: {
                "completed": True,
                "deaths": 0,
                "duration_minutes": 8,
            },
            2: {
                "completed": True,
                "deaths": 0,
                "duration_minutes": 10,
            },
            3: {
                "completed": True,
                "deaths": 2,
                "duration_minutes": 15,
            },
        },

        "player_002": {
            1: {
                "completed": True,
                "deaths": 0,
                "duration_minutes": 7,
            },
            2: {
                "completed": True,
                "deaths": 1,
                "duration_minutes": 12,
            },
            3: {
                "completed": False,
                "deaths": 1,
                "duration_minutes": 6,
            },
        },

        "player_003": {
            1: {
                "completed": True,
                "deaths": 0,
                "duration_minutes": 9,
            },
            2: {
                "completed": True,
                "deaths": 0,
                "duration_minutes": 11,
            },
            3: {
                "completed": True,
                "deaths": 3,
                "duration_minutes": 18,
            },
        },

        "player_004": {
            1: {
                "completed": True,
                "deaths": 0,
                "duration_minutes": 6,
            },
            2: {
                "completed": False,
                "deaths": 2,
                "duration_minutes": 8,
            },
        },

        "player_005": {
            1: {
                "completed": True,
                "deaths": 0,
                "duration_minutes": 8,
            },
            2: {
                "completed": True,
                "deaths": 0,
                "duration_minutes": 9,
            },
            3: {
                "completed": True,
                "deaths": 0,
                "duration_minutes": 12,
            },
        },

        "player_006": {
            1: {
                "completed": True,
                "deaths": 0,
                "duration_minutes": 7,
            },
            2: {
                "completed": True,
                "deaths": 1,
                "duration_minutes": 13,
            },
            3: {
                "completed": True,
                "deaths": 1,
                "duration_minutes": 14,
            },
        },
    }

    for index, (player_id, level_data) in enumerate(players.items()):
        player_start = base_time + timedelta(hours=index)

        player_events = generate_player_events(
            player_id,
            player_start,
            level_data,
        )

        all_events.extend(player_events)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Remove previous mock dataset so the script is safe to run again.
    cursor.execute(
        "DELETE FROM events WHERE game_id = %s;",
        (GAME_ID,),
    )

    insert_query = """
        INSERT INTO events (
            event,
            player_id,
            game_id,
            timestamp,
            level
        )
        VALUES (%s, %s, %s, %s, %s);
    """

    cursor.executemany(insert_query, all_events)

    conn.commit()

    cursor.close()
    conn.close()

    print(
        f"Inserted {len(all_events)} mock events "
        f"for game '{GAME_ID}'."
    )


if __name__ == "__main__":
    main()