# QuestMetrix Godot SDK

The QuestMetrix Godot SDK allows a Godot game to send gameplay
telemetry events to a QuestMetrix backend.

## Requirements

- Godot 4.x
- A running QuestMetrix backend

## Installation

1. Copy `QuestMetrix.gd` into your Godot project's `sdk/` folder.
2. Open Project Settings.
3. Go to Globals > Autoload.
4. Add `QuestMetrix.gd`.
5. Set the Autoload name to `QuestMetrix`.

## Configuration

Configure:

- API base URL
- game ID
- player ID

## Sending an Event

From any GDScript:

```gdscript
QuestMetrix.track("enemy_killed")
```

Optional event data can be supplied:

```
QuestMetrix.track(
    "enemy_killed",
    {
        "enemy_type": "goblin"
    }
)
```

## Event Flow

```
Godot Game
    ↓
QuestMetrix.track()
    ↓
QuestMetrix SDK
    ↓
POST /events
    ↓
QuestMetrix Backend
```

## Error Handling

If the QuestMetrix backend cannot be reached, the SDK logs
the error and does not crash the game.

The current SDK does not retry failed requests or queue
events for later delivery.

These features are outside the scope of the current SDK version.
