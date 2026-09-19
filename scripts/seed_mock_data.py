import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
API_KEY = "qm_test_key_12345"
GAME_ID = "mock_analytics_game"

events = []

base_time = datetime(2026, 9, 15, 10, 0, 0)

players = [
    "player_1",
    "player_2",
    "player_3",
    "player_4",
    "player_5",
]

levels = [1, 2, 3, 4, 5]


def add_event(event, player_id, timestamp, level):
    events.append({
        "event": event,
        "player_id": player_id,
        "game_id": GAME_ID,
        "timestamp": timestamp.isoformat(),
        "level": level,
    })


# Player 1: successful player
for level in levels:
    start = base_time + timedelta(minutes=level * 10)

    add_event("player_started_level", "player_1", start, level)
    add_event("enemy_killed", "player_1", start + timedelta(minutes=2), level)
    add_event("item_collected", "player_1", start + timedelta(minutes=3), level)
    add_event("level_completed", "player_1", start + timedelta(minutes=5), level)


# Player 2: dies occasionally
for level in [1, 2, 3]:
    start = base_time + timedelta(hours=1, minutes=level * 10)

    add_event("player_started_level", "player_2", start, level)
    add_event("enemy_killed", "player_2", start + timedelta(minutes=2), level)

    if level == 2:
        add_event("player_died", "player_2", start + timedelta(minutes=3), level)
    else:
        add_event("level_completed", "player_2", start + timedelta(minutes=5), level)


# Player 3: starts but quits
for level in [1, 2]:
    start = base_time + timedelta(hours=2, minutes=level * 15)

    add_event("player_started_level", "player_3", start, level)
    add_event("item_collected", "player_3", start + timedelta(minutes=2), level)
    add_event("player_quit", "player_3", start + timedelta(minutes=4), level)


# Player 4: dialogue-heavy player
for level in [1, 2, 3]:
    start = base_time + timedelta(hours=3, minutes=level * 10)

    add_event("player_started_level", "player_4", start, level)
    add_event("dialogue_selected", "player_4", start + timedelta(minutes=1), level)
    add_event("dialogue_selected", "player_4", start + timedelta(minutes=2), level)
    add_event("level_completed", "player_4", start + timedelta(minutes=6), level)


# Player 5: returns on later days
for day in [0, 1, 2]:
    start = base_time + timedelta(days=day, hours=4)

    add_event("player_started_level", "player_5", start, 1)
    add_event("enemy_killed", "player_5", start + timedelta(minutes=2), 1)
    add_event("level_completed", "player_5", start + timedelta(minutes=5), 1)


print(f"Generated {len(events)} events.")

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}

successful = 0
failed = 0

for event in events:
    try:
        response = requests.post(
            f"{BASE_URL}/events",
            json=event,
            headers=headers,
        )

        if response.status_code == 200:
            successful += 1
        else:
            failed += 1
            print(
                f"Failed: {response.status_code} "
                f"{response.text}"
            )

    except requests.RequestException as exc:
        failed += 1
        print(f"Request failed: {exc}")

print(f"Successfully queued: {successful}")
print(f"Failed: {failed}")