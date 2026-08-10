# QuestMetrix --- Project Documentation & Study Notes
**Date**: 11-08-2026

## 1. Project Identity

**Project name:** QuestMetrix\
**Short name:** QM\
**Project type:** Game Telemetry & Analytics Platform\
**Repository name:** `questmetrix`

QuestMetrix is a software infrastructure project for game developers. It
is not primarily a game itself. Its purpose is to let a game send
gameplay events to a backend, store those events, process them into
useful analytics, and eventually display those analytics through a
developer dashboard.

The planned architecture is:

``` text
Game
  ↓
QuestMetrix SDK
  ↓
Event API
  ↓
Message Queue
  ↓
Processing Workers
  ↓
Database / Cache
  ↓
Analytics Dashboard
```

The project is intended to explore backend engineering, data
engineering, APIs, asynchronous processing, caching, authentication,
real-time communication, testing, observability, and performance
engineering.

------------------------------------------------------------------------

# 2. Why This Project Exists

The project was chosen because the existing portfolio already
demonstrates game development, frontend development, enterprise
software, VR, and compiler/language work.

The comparatively missing areas were:

-   backend engineering
-   APIs
-   databases
-   networking
-   asynchronous processing
-   caching
-   distributed systems
-   authentication
-   observability
-   performance/load testing
-   system architecture

QuestMetrix is therefore intended to add:

> **Game Development + Backend Engineering + Data Engineering +
> Systems**

The important distinction is:

> **We are not making another game. We are building infrastructure that
> can be used by games.**

------------------------------------------------------------------------

# 3. Core Problem

A game produces useful information while a player is playing.

Examples:

``` text
player_started_level
enemy_killed
item_collected
player_died
level_completed
player_quit
```

A developer may want to know:

``` text
How many players started Level 3?
How many completed it?
How many times did they die?
Which enemy killed them most often?
Where are players quitting?
How long does the level take?
```

QuestMetrix collects the raw gameplay events needed to answer questions
like these.

The basic idea is:

``` text
Raw gameplay activity
        ↓
Telemetry events
        ↓
Storage
        ↓
Processing
        ↓
Analytics
        ↓
Developer insight
```

------------------------------------------------------------------------

# 4. Project Scope

## 4.1 Initial scope

The first version is intentionally small.

The first goal is to make one event travel through the complete basic
backend pipeline:

``` text
Event
  ↓
FastAPI
  ↓
PostgreSQL
  ↓
Retrieve event through API
```

The first event is:

``` text
enemy_killed
```

## 4.2 Planned scope

After the basic backend works, the project will gradually gain:

### SDK

A Godot SDK that allows a game developer to write something like:

``` gdscript
QuestMetrix.track("enemy_killed")
```

### Backend

The API will eventually support endpoints such as:

``` text
POST /events
GET  /events
GET  /players
GET  /games
```

### Database

PostgreSQL will store telemetry data.

### Dashboard

A React dashboard will eventually show:

-   event counts
-   player statistics
-   level progression
-   retention
-   session information
-   difficulty indicators
-   other analytics

### Scalable infrastructure

Later stages may introduce:

-   Redis
-   message queues
-   background workers
-   rate limiting
-   authentication
-   API keys
-   WebSockets
-   Docker
-   CI/CD
-   automated testing
-   logging
-   metrics
-   load testing
-   database migrations

### Advanced feature

A later differentiating feature is session/replay analysis.

Instead of storing only:

``` text
player_died
```

the platform could represent:

``` text
START LEVEL
    ↓
MOVE
    ↓
COLLECT ITEM
    ↓
FIGHT ENEMY
    ↓
LOSE HP
    ↓
MOVE
    ↓
DIE
```

This could eventually be visualized as a player session timeline.

------------------------------------------------------------------------

# 5. Planned Architecture

The eventual architecture is:

``` text
                    GAME
                     │
                     ▼
             QuestMetrix SDK
                     │
                     ▼
                 Event API
                     │
                     ▼
               Message Queue
                     │
                     ▼
             Processing Workers
                 │        │
                 │        └──────► Redis
                 │
                 ▼
              PostgreSQL
                     │
                     ▼
           Analytics / API Layer
                     │
                     ▼
             React Dashboard
```

The architecture will become more complicated gradually.

**Do not implement the entire architecture at once.**

The project is being built incrementally so that every new component is
understood before another component is added.

------------------------------------------------------------------------

# 6. Current Technology Stack

## Currently used

  -----------------------------------------------------------------------
  Component               Technology              Purpose
  ----------------------- ----------------------- -----------------------
  Backend                 Python                  Backend programming
                                                  language

  API framework           FastAPI                 HTTP API

  Data validation         Pydantic                Validate incoming event
                                                  data

  Database                PostgreSQL 18           Persistent event
                                                  storage

  PostgreSQL driver       psycopg2-binary         Python → PostgreSQL
                                                  communication

  Environment variables   python-dotenv           Load database
                                                  configuration from
                                                  `.env`

  API testing             FastAPI Swagger/OpenAPI Manually test endpoints
                          docs                    

  IDE                     VS Code                 Development

  Version control         Git                     Track changes

  Remote repository       GitHub                  Store project source
  -----------------------------------------------------------------------

## Planned

  Component           Planned technology
  ------------------- -----------------------------------
  Game SDK            Godot / GDScript
  Dashboard           React
  Cache               Redis
  Async processing    Message queue + workers
  Real-time updates   WebSockets
  Containerization    Docker
  CI/CD               GitHub Actions or equivalent
  Testing             Unit + integration + load testing

------------------------------------------------------------------------

# 7. Repository Setup

## Step 1 --- Create GitHub repository

A GitHub repository named:

``` text
questmetrix
```

was created.

The repository was initialized with:

-   README
-   Python `.gitignore`

### Why?

GitHub is the remote home of the project.

Git tracks the history of the project locally, while GitHub stores and
displays that history remotely.

------------------------------------------------------------------------

# 8. Local Repository Setup

The repository was cloned onto the computer and opened in VS Code.

The project structure was created as:

``` text
questmetrix/
├── backend/
├── dashboard/
├── database/
├── docs/
├── sdk/
├── tests/
├── .gitignore
├── LICENSE
└── README.md
```

### Why create these folders early?

They represent the major components of the eventual system.

``` text
backend/    → API and server logic
dashboard/  → React analytics UI
database/   → database-related files/migrations
docs/       → project documentation
sdk/        → game integration code
tests/      → automated tests
```

Not every folder is populated yet.

------------------------------------------------------------------------

# 9. Git Branch Setup

A development branch was created:

``` text
dev
```

The intended basic structure is:

``` text
main
  ↑
dev
  ↑
feature branches
```

The basic Git workflow is:

``` bash
git status
git add .
git commit -m "message"
git push
```

Meanings:

-   `git status` --- shows what changed.
-   `git add .` --- stages changes.
-   `git commit` --- creates a version/checkpoint.
-   `git push` --- uploads local commits to GitHub.
-   `git pull` --- downloads remote changes.

------------------------------------------------------------------------

# 10. README and License

The repository contains:

``` text
README.md
LICENSE
```

The README was structured around:

-   Overview
-   Problem
-   Goals
-   Architecture
-   Tech Stack
-   Project Structure
-   Getting Started
-   Features
-   Roadmap
-   Testing
-   License

The README deliberately separates:

``` text
Currently Implemented
```

from:

``` text
Planned
```

This prevents the documentation from claiming that unfinished features
already exist.

The project uses the MIT License.

------------------------------------------------------------------------

# 11. Python Backend Setup

The backend is located at:

``` text
questmetrix/backend/
```

A Python virtual environment was created:

``` text
backend/venv/
```

The virtual environment isolates this project's Python dependencies.

It should not be committed to GitHub.

The `.gitignore` should contain:

``` gitignore
venv/
__pycache__/
*.pyc
.env
```

------------------------------------------------------------------------

# 12. FastAPI Setup

FastAPI was installed in the virtual environment.

The backend file is:

``` text
backend/main.py
```

The initial backend was:

``` python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "QuestMetrix backend is running!"}
```

The server is started with:

``` bash
uvicorn main:app --reload
```

The command means:

``` text
uvicorn main:app
        │    │
        │    └── object named "app"
        │
        └────── Python module "main"
```

Therefore Uvicorn finds `main.py` and then the FastAPI object named
`app`.

`--reload` automatically restarts the development server when code
changes.

------------------------------------------------------------------------

# 13. First Backend Verification

The server successfully started at:

``` text
http://127.0.0.1:8000
```

The root endpoint:

``` text
GET /
```

returns:

``` json
{
  "message": "QuestMetrix backend is running!"
}
```

This proved that the FastAPI server was working.

A browser request for:

``` text
/favicon.ico
```

returned 404. This was harmless because no favicon had been created.

------------------------------------------------------------------------

# 14. PostgreSQL Installation

PostgreSQL 18 was installed.

The PostgreSQL server uses the standard port:

``` text
5432
```

The PostgreSQL Stack Builder appeared after installation.

Stack Builder is optional and was not needed for QuestMetrix at this
stage, so it was closed.

The important result was that PostgreSQL itself was installed and
running.

------------------------------------------------------------------------

# 15. pgAdmin Verification

pgAdmin 4 was opened.

The server appeared as:

``` text
PostgreSQL 18
```

The server tree contained:

``` text
Servers
└── PostgreSQL 18
    ├── Databases
    ├── Login/Group Roles
    └── Tablespaces
```

This confirmed that PostgreSQL was accessible.

------------------------------------------------------------------------

# 16. QuestMetrix Database Creation

A PostgreSQL database named:

``` text
questmetrix
```

was created.

The resulting structure initially looked like:

``` text
Databases
├── postgres
└── questmetrix
```

### Why?

The PostgreSQL server is not itself the application's database.

The hierarchy is:

``` text
PostgreSQL Server
       ↓
questmetrix database
       ↓
tables
       ↓
rows
```

The `questmetrix` database is where the application's telemetry data
will live.

------------------------------------------------------------------------

# 17. First Telemetry Event

Before connecting the database to the backend, the first event format
was defined.

A file was created:

``` text
backend/event_schema.json
```

It contains the sample:

``` json
{
    "event": "enemy_killed",
    "player_id": "player_001",
    "game_id": "demo_game",
    "timestamp": "2026-08-11T00:00:00Z",
    "level": 1
}
```

This is currently a sample event representation. It is not yet a
complete formal event-schema system.

------------------------------------------------------------------------

# 18. Understanding the Event Fields

### `event`

Example:

``` text
enemy_killed
```

What happened?

### `player_id`

Example:

``` text
player_001
```

Which player generated it?

### `game_id`

Example:

``` text
demo_game
```

Which game generated it?

### `timestamp`

Example:

``` text
2026-08-11T00:00:00Z
```

When did it happen?

### `level`

Example:

``` text
1
```

Which level was the player in?

The event therefore answers:

``` text
WHAT?
WHO?
WHICH GAME?
WHEN?
WHERE IN THE GAME?
```

------------------------------------------------------------------------

# 19. Why the Event Was Defined First

The event represents the data entering the system.

The database table represents how that data is stored.

They are related but conceptually different:

``` text
Incoming event
      ↓
Data contract
      ↓
FastAPI validation
      ↓
Database storage model
```

Defining the data first prevents blindly creating storage without
knowing what it must contain.

------------------------------------------------------------------------

# 20. Pydantic Event Model

Pydantic was installed.

The backend was extended with:

``` python
from pydantic import BaseModel
```

and:

``` python
class Event(BaseModel):
    event: str
    player_id: str
    game_id: str
    timestamp: str
    level: int
```

This describes what a valid incoming QuestMetrix event looks like.

For example:

``` json
{
  "event": "enemy_killed",
  "player_id": "player_001",
  "game_id": "demo_game",
  "timestamp": "2026-08-11T00:00:00Z",
  "level": 1
}
```

matches the model.

------------------------------------------------------------------------

# 21. First API Endpoint --- POST /events

The first event endpoint was created:

``` python
@app.post("/events")
def receive_event(event: Event):
    return {
        "message": "Event received successfully!",
        "event": event
    }
```

Initially, this endpoint only received and validated an event.

It did not store it yet.

The flow was:

``` text
JSON
 ↓
POST /events
 ↓
FastAPI
 ↓
Pydantic validation
 ↓
JSON response
```

------------------------------------------------------------------------

# 22. Testing POST /events

FastAPI automatically provides interactive documentation at:

``` text
http://127.0.0.1:8000/docs
```

The endpoint was tested there with:

``` json
{
  "event": "enemy_killed",
  "player_id": "player_001",
  "game_id": "demo_game",
  "timestamp": "2026-08-11T00:00:00Z",
  "level": 1
}
```

The API successfully returned the event.

This proved:

``` text
POST request
     ↓
FastAPI
     ↓
Pydantic validation
     ↓
JSON response
```

was working.

------------------------------------------------------------------------

# 23. PostgreSQL Events Table

The first table was created in the `questmetrix` database:

``` text
events
```

SQL used:

``` sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    event VARCHAR(100) NOT NULL,
    player_id VARCHAR(100) NOT NULL,
    game_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    level INTEGER NOT NULL
);
```

Conceptually:

``` text
events
------------------------------------------------
id
event
player_id
game_id
timestamp
level
------------------------------------------------
```

### Column purposes

`id` --- unique ID for each event.

`event` --- what happened.

`player_id` --- which player generated it.

`game_id` --- which game generated it.

`timestamp` --- when it happened.

`level` --- level associated with the event.

`NOT NULL` means those values cannot be missing.

------------------------------------------------------------------------

# 24. Connecting FastAPI to PostgreSQL

The following packages were installed:

``` bash
pip install psycopg2-binary python-dotenv
```

Dependencies were then saved:

``` bash
pip freeze > requirements.txt
```

### psycopg2-binary

Allows Python to communicate with PostgreSQL:

``` text
Python
  ↓
psycopg2
  ↓
PostgreSQL
```

### python-dotenv

Loads database configuration from `.env`.

------------------------------------------------------------------------

# 25. Database Configuration

A file was created:

``` text
backend/.env
```

with:

``` env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=questmetrix
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD
```

The real password is stored locally.

`.env` must not be uploaded to GitHub.

Therefore `.gitignore` contains:

``` gitignore
.env
```

This prevents credentials from entering source control.

------------------------------------------------------------------------

# 26. Loading Environment Variables

The backend uses:

``` python
from dotenv import load_dotenv

load_dotenv()
```

Then:

``` python
os.getenv("DB_HOST")
os.getenv("DB_PORT")
os.getenv("DB_NAME")
os.getenv("DB_USER")
os.getenv("DB_PASSWORD")
```

are used for the database connection.

The flow is:

``` text
.env
 ↓
load_dotenv()
 ↓
environment variables
 ↓
database connection
```

VS Code displayed a notification saying terminal environment-file
injection was disabled.

This was not an error.

It did not affect the project because `python-dotenv` loads the `.env`
file from inside the Python application.

------------------------------------------------------------------------

# 27. Database Connection Function

The backend contains:

``` python
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
```

Its purpose is:

> Open a connection from FastAPI/Python to the QuestMetrix PostgreSQL
> database.

Conceptually:

``` text
FastAPI
   ↓
get_db_connection()
   ↓
PostgreSQL
```

------------------------------------------------------------------------

# 28. POST /events Now Stores Data

The POST endpoint was changed so that it performs an SQL `INSERT`.

Conceptually:

``` text
POST /events
      ↓
Pydantic validation
      ↓
Database connection
      ↓
INSERT INTO events
      ↓
COMMIT
      ↓
Event stored
```

The SQL uses parameters rather than concatenating user input directly
into the SQL statement.

After the insertion:

-   the transaction is committed
-   the cursor is closed
-   the database connection is closed

------------------------------------------------------------------------

# 29. Verifying Storage

In pgAdmin, the following was executed:

``` sql
SELECT * FROM events;
```

The previously submitted event appeared in the table.

This proved:

``` text
JSON event
    ↓
POST /events
    ↓
FastAPI
    ↓
Pydantic
    ↓
psycopg2
    ↓
PostgreSQL
    ↓
events table
```

was working.

This is the first real persistent data pipeline in QuestMetrix.

------------------------------------------------------------------------

# 30. GET /events

A retrieval endpoint was then added:

``` text
GET /events
```

Its purpose is to read stored telemetry from PostgreSQL.

The implementation concept is:

``` python
@app.get("/events")
def get_events():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, event, player_id, game_id, timestamp, level
        FROM events
        ORDER BY id;
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    events = []

    for row in rows:
        events.append({
            "id": row[0],
            "event": row[1],
            "player_id": row[2],
            "game_id": row[3],
            "timestamp": row[4],
            "level": row[5]
        })

    return {"events": events}
```

The flow is:

``` text
GET /events
     ↓
FastAPI
     ↓
SELECT
     ↓
PostgreSQL
     ↓
fetch rows
     ↓
Python dictionaries
     ↓
JSON response
```

------------------------------------------------------------------------

# 31. Why GET /events Matters

Before this endpoint:

``` text
Data could enter the system
        ↓
Data was stored
```

but there was no API endpoint for retrieving it.

Now:

``` text
POST /events → WRITE
GET  /events → READ
```

The basic backend data flow is complete.

------------------------------------------------------------------------

# 32. Multiple Event Test

A second event was submitted:

``` json
{
  "event": "level_completed",
  "player_id": "player_001",
  "game_id": "demo_game",
  "timestamp": "2026-08-11T00:05:00Z",
  "level": 1
}
```

Then:

``` text
GET /events
```

was used to retrieve the stored events.

This verified that the backend could handle multiple event records.

------------------------------------------------------------------------

# 33. Current Backend Architecture

At this point:

``` text
                 QUESTMETRIX

          ┌────────────────────┐
          │      FastAPI       │
          │                    │
          │ GET /              │
          │ POST /events       │
          │ GET /events        │
          └─────────┬──────────┘
                    │
                    ▼
          ┌────────────────────┐
          │    PostgreSQL      │
          │                    │
          │  questmetrix DB    │
          │      events        │
          └────────────────────┘
```

Implemented:

-   GitHub repository
-   project structure
-   `dev` branch
-   README
-   MIT license
-   Python virtual environment
-   FastAPI server
-   Pydantic event model
-   sample event definition
-   PostgreSQL 18
-   `questmetrix` database
-   `events` table
-   `.env` configuration
-   PostgreSQL Python driver
-   `POST /events`
-   `GET /events`
-   persistent telemetry storage
-   manual API testing
-   database verification

------------------------------------------------------------------------

# 34. Current Project Folder Structure

The intended structure is:

``` text
questmetrix/
│
├── backend/
│   ├── __pycache__/
│   ├── venv/
│   ├── .env
│   ├── event_schema.json
│   ├── main.py
│   └── requirements.txt
│
├── dashboard/
├── database/
├── docs/
├── sdk/
├── tests/
│
├── .gitignore
├── LICENSE
└── README.md
```

Important:

``` text
venv/
__pycache__/
.env
```

should not be committed.

------------------------------------------------------------------------

# 35. What Has NOT Been Built Yet

These are planned, not implemented:

-   Godot SDK
-   automatic game event collection
-   React dashboard
-   analytics calculations
-   player analytics
-   session analytics
-   retention analytics
-   Redis
-   message queue
-   background workers
-   authentication
-   API keys
-   rate limiting
-   WebSockets
-   Docker
-   CI/CD
-   automated testing
-   logging/monitoring
-   database migrations
-   load testing
-   session/replay visualization

Do not describe these as completed features on the resume or README.

------------------------------------------------------------------------

# 36. Immediate Next Step

The next logical step is the **Godot SDK**.

Currently we simulate a game by manually entering JSON into FastAPI's
Swagger interface:

``` text
Human
 ↓
Swagger /docs
 ↓
POST /events
 ↓
FastAPI
 ↓
PostgreSQL
```

The goal is to replace that with:

``` text
Godot Game
   ↓
QuestMetrix SDK
   ↓
POST /events
   ↓
FastAPI
   ↓
PostgreSQL
```

The first SDK should eventually provide something like:

``` gdscript
QuestMetrix.track("enemy_killed")
```

The first SDK milestone should be tiny:

> Make a test Godot project generate one event and send it to the
> existing backend.

------------------------------------------------------------------------

# 37. Planned Development Sequence

``` text
PHASE 1 — FOUNDATION
        ↓
Git + repository + documentation
        ↓
FastAPI
        ↓
PostgreSQL
        ↓
Event schema
        ↓
POST /events
        ↓
GET /events

PHASE 2 — GAME INTEGRATION
        ↓
Godot test project
        ↓
QuestMetrix SDK
        ↓
track()
        ↓
Godot → FastAPI

PHASE 3 — ANALYTICS
        ↓
Event aggregation
        ↓
Player statistics
        ↓
Level statistics
        ↓
Session statistics

PHASE 4 — DASHBOARD
        ↓
React
        ↓
Raw event view
        ↓
Metrics
        ↓
Charts

PHASE 5 — SCALABILITY
        ↓
Redis
        ↓
Message queue
        ↓
Workers
        ↓
Rate limiting
        ↓
Authentication

PHASE 6 — REAL-TIME / ADVANCED
        ↓
WebSockets
        ↓
Session/replay analysis

PHASE 7 — ENGINEERING HARDENING
        ↓
Tests
        ↓
Logging
        ↓
Metrics
        ↓
Docker
        ↓
CI/CD
        ↓
Load testing
```

------------------------------------------------------------------------

# 38. Learning Rule for This Project

Because this is a first major solo project, every new technology should
be understood through four questions:

### 1. What is it?

Example:

> PostgreSQL is the database storing telemetry events.

### 2. Why do we need it?

> FastAPI alone does not permanently store the events.

### 3. Where does it sit?

``` text
FastAPI → PostgreSQL
```

### 4. What problem does it solve?

> Persistent structured storage and retrieval.

Use this framework whenever a new component is introduced.

------------------------------------------------------------------------

# 39. Core Data Flow to Remember

The most important concept right now is how one event travels.

Eventually:

``` text
Godot
 ↓
QuestMetrix SDK
 ↓
HTTP POST
 ↓
FastAPI
 ↓
Pydantic validation
 ↓
psycopg2
 ↓
PostgreSQL
 ↓
events table
```

Then the reverse direction:

``` text
events table
 ↓
PostgreSQL
 ↓
psycopg2
 ↓
FastAPI
 ↓
GET /events
 ↓
JSON
 ↓
Dashboard
```

This is the fundamental architecture currently implemented.

------------------------------------------------------------------------

# 40. Current Milestone

## Milestone 1 --- Basic Telemetry Backend

**Status: COMPLETE**

Acceptance criteria:

-   [x] Backend server starts
-   [x] FastAPI root endpoint works
-   [x] PostgreSQL is running
-   [x] QuestMetrix database exists
-   [x] `events` table exists
-   [x] Event format defined
-   [x] FastAPI validates event data
-   [x] `POST /events` accepts events
-   [x] Events are inserted into PostgreSQL
-   [x] `GET /events` retrieves stored events
-   [x] Multiple events can be stored and retrieved

## Next milestone

### Milestone 2 --- Godot SDK Integration

Goal:

> Send a real gameplay event from a Godot project into QuestMetrix
> without manually using Swagger.

------------------------------------------------------------------------

# 41. Git Commit Strategy

Each meaningful milestone should have its own commit.

Examples:

``` bash
git add .
git commit -m "chore: initialize project structure"
```

``` bash
git add .
git commit -m "feat: add FastAPI backend"
```

``` bash
git add .
git commit -m "feat: define telemetry event model"
```

``` bash
git add .
git commit -m "feat: store telemetry events in PostgreSQL"
```

``` bash
git add .
git commit -m "feat: add telemetry event retrieval endpoint"
```

Future examples:

``` text
feat: add Godot telemetry SDK
feat: send events from Godot
feat: add analytics aggregation
feat: create analytics dashboard
feat: add Redis caching
feat: add asynchronous event processing
```

The Git history should tell the story of how the project was built.

------------------------------------------------------------------------

# 42. Current Mental Model

A concise explanation of the project at the current stage:

> QuestMetrix is a game telemetry platform. A game generates gameplay
> events such as `enemy_killed` or `level_completed`. These events will
> eventually be captured by a Godot SDK and sent to a FastAPI backend.
> The backend validates the events and stores them in PostgreSQL.
> Currently, the backend already supports manually submitting and
> retrieving telemetry events through `POST /events` and `GET /events`.
> The next step is replacing manual API testing with a real Godot SDK.

------------------------------------------------------------------------

# 43. Final Current-State Summary

QuestMetrix has moved from:

``` text
IDEA
```

to:

``` text
WORKING BACKEND
```

Current implementation:

``` text
             QUESTMETRIX v0.1

        ┌────────────────────┐
        │     API CLIENT     │
        │                    │
        │ FastAPI /docs      │
        └─────────┬──────────┘
                  │
             POST /events
                  │
                  ▼
        ┌────────────────────┐
        │      FastAPI       │
        │                    │
        │ Pydantic validation│
        └─────────┬──────────┘
                  │
                  ▼
        ┌────────────────────┐
        │    PostgreSQL      │
        │                    │
        │ questmetrix        │
        │   └── events       │
        └─────────┬──────────┘
                  │
             GET /events
                  │
                  ▼
              JSON DATA
```

The next transformation is:

``` text
CURRENT

Swagger
   ↓
FastAPI
   ↓
PostgreSQL


NEXT

Godot Game
   ↓
QuestMetrix SDK
   ↓
FastAPI
   ↓
PostgreSQL
```

That is the next concrete development target.
