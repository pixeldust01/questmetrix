# Technical Design Document (TDD): QuestMetrix
**Version:** v0.1 · **Date:** 11 Aug 2026 · **Status:** Living document — update as milestones close

---

## 1. Overview

**Like you're 5:** Imagine your favorite game could send you a little postcard every time something happens inside it — "a monster died!", "you finished the level!". QuestMetrix is the mailbox that catches those postcards, the filing cabinet that keeps them safe, and (eventually) the picture book that turns a big pile of postcards into charts a grown-up can actually understand.

**More precisely:** QuestMetrix is a game telemetry and analytics platform for game developers. It is **infrastructure**, not a game — its job is to receive gameplay events from a game, store them, turn them into useful statistics, and display those statistics through a dashboard.

The full journey a single postcard (event) takes, end to end:

```text
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

Right now, only the middle part of that chain exists (game events go in via a form, get checked, and get filed away). Everything before and after it is being added piece by piece — on purpose, not all at once — so every new part is understood before the next one is bolted on.

---

## 2. Goals & Scope

**Like you're 5:** First we taught the mailbox to accept one postcard and file it correctly. That's done. Now we're slowly teaching it to also read the return address, sort postcards into folders, and eventually draw pictures from what's inside them.

### ✅ Completed Scope — Milestone 1
- A working backend: FastAPI + PostgreSQL.
- A single event type (`enemy_killed`) can travel all the way from a request → validation → storage → retrieval.
- Endpoints: `POST /events` (write a postcard), `GET /events` (read all the postcards back).

### ⏳ Planned Scope
- **SDK Integration** — a Godot plug-in so a real game can send events automatically, instead of a human typing JSON into a web form.
- **Analytics Layer** — turning raw postcards into answers like "how many players died on Level 3?"
- **Dashboard** — a React website that shows those answers as numbers and charts.
- **Scalable Infrastructure** — Redis, a message queue, and background workers, so the mailbox doesn't get overwhelmed if a lot of postcards arrive at once.
- **Advanced Feature** — session/replay: instead of one postcard per event, stringing them together into a story of what one player did, in order.
- **Engineering Hardening** — tests, logging, Docker, CI/CD, load testing: making sure the whole system is trustworthy, not just "it worked once on my laptop."

**Non-goal (important):** QuestMetrix is not, and is not trying to become, a game. It's the plumbing behind a game.

---

## 3. System Architecture

### 3.1 Current architecture (as built today)

**Like you're 5:** Right now, a person pretends to be the game. They fill out a little form (Swagger), it gets checked by a strict guard (Pydantic), and then it's filed into a big cabinet (PostgreSQL).

```text
Client (Swagger / Postman / manual JSON)
         │
         ▼
     FastAPI
   (Pydantic validation)
         │
         ▼
   PostgreSQL
  (questmetrix DB → events table)
```

### 3.2 Target architecture (where the project is heading)

**Like you're 5:** Eventually the game itself sends the postcard (no human typing it in). The postcard doesn't go straight into the filing cabinet — it first joins a line (the queue), and a helper (the worker) picks it up and files it properly, sometimes also jotting a quick sticky note (Redis cache) for things that need to be looked up fast. Then a picture book (the dashboard) reads the filing cabinet and draws charts, and can even get updates live, like a phone call that never hangs up (WebSockets).

```text
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
                 │        └──────► Redis (cache)
                 │
                 ▼
              PostgreSQL
                     │
                     ▼
           Analytics / API Layer
                     │
                     ▼
             React Dashboard
          (+ WebSockets for live updates)
```

**Important rule the project follows:** *Do not build the whole target architecture at once.* Each box above gets added only after the boxes before it are working and understood. That's why the roadmap is split into phases instead of one giant leap.

---

## 4. Technology Stack

**Like you're 5:** Every tool here has one job, like workers in a small shop.

### Currently used

| Component | Technology | Like you're 5 | What it actually does |
|---|---|---|---|
| Language | Python | The language everyone in the shop speaks | Backend programming language |
| API framework | FastAPI | The front-desk clerk who takes requests and hands back answers | Handles HTTP requests/responses |
| Validation | Pydantic | The bouncer checking your ID has the right shape before letting you in | Validates incoming event data against a schema |
| Database | PostgreSQL 18 | A giant filing cabinet that never forgets what you put in it | Persistent storage for events |
| DB driver | psycopg2-binary | The delivery truck between Python and the filing cabinet | Lets Python talk to PostgreSQL |
| Config loader | python-dotenv | A private notebook that whispers passwords to the program instead of writing them on the wall | Loads DB config from `.env` without hardcoding secrets |
| API testing | FastAPI Swagger/OpenAPI docs | A practice counter where you can pretend to be a customer | Manual endpoint testing at `/docs` |
| Version control | Git | A time machine for your code | Tracks every change ever made |
| Remote repo | GitHub | A cloud backup of the time machine | Stores and displays project history |

### Planned

| Component | Planned technology | Like you're 5 |
|---|---|---|
| Game SDK | Godot / GDScript | The actual playground where the game runs and mails postcards on its own |
| Dashboard | React | The picture book that turns numbers into charts |
| Cache | Redis | A sticky-note board next to the desk — very fast, but notes are meant to be short-lived |
| Async processing | Message queue + workers | A waiting line, plus a helper who processes one postcard at a time so none get lost |
| Real-time updates | WebSockets | A phone call that stays open instead of texting back and forth |
| Containerization | Docker | A lunchbox with everything already packed inside, so it works the same on any desk |
| CI/CD | GitHub Actions (or similar) | A robot assistant that checks your homework every time you turn something in |
| Testing | Unit + integration + load testing | Practice runs, plus a stress test to see how much weight the bridge can hold |

---

## 5. Data Model

### 5.1 Event schema (implemented)

**Like you're 5:** Every postcard has to have the same five things written on it, or the bouncer (Pydantic) won't let it through the door.

```python
class Event(BaseModel):
    event: str        # WHAT happened?
    player_id: str     # WHO caused it?
    game_id: str        # WHICH game sent it?
    timestamp: str        # WHEN did it happen?
    level: int              # WHERE in the game (which level)?
```

Sample postcard:

```json
{
  "event": "enemy_killed",
  "player_id": "player_001",
  "game_id": "demo_game",
  "timestamp": "2026-08-11T00:00:00Z",
  "level": 1
}
```

### 5.2 Database table (implemented)

**Like you're 5:** This is the shape of the drawer inside the filing cabinet where postcards get stored.

```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    event VARCHAR(100) NOT NULL,
    player_id VARCHAR(100) NOT NULL,
    game_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    level INTEGER NOT NULL
);
```

| Column | Like you're 5 |
|---|---|
| `id` | A ticket number, automatically stamped on each postcard |
| `event` | What happened |
| `player_id` | The player's name tag |
| `game_id` | Which game this came from |
| `timestamp` | The clock-stamp of when it happened |
| `level` | Which room (level) of the game it happened in |

`NOT NULL` means the bouncer won't accept a postcard that's missing any of these — it has to be complete.

### 5.3 Planned data model extensions

- **Sessions** — grouping a player's events that happen close together in time into one "play session" (like grouping all the postcards someone mailed during one visit to the post office).
- **Retention** — tracking whether a player came back and mailed more postcards on a later day (did they visit the game again?).
- **Replay** — keeping the *order* of a player's events, so instead of a pile of postcards you get a story: START LEVEL → MOVE → COLLECT ITEM → FIGHT ENEMY → LOSE HP → DIE.

---

## 6. API Endpoints

### Implemented

| Endpoint | Like you're 5 | Details |
|---|---|---|
| `GET /` | "Are you awake?" "Yes!" | Health check — confirms the backend is running |
| `POST /events` | Drop a postcard in the mailbox | Validates (Pydantic) and inserts one event into PostgreSQL |
| `GET /events` | Ask to see every postcard ever filed | Returns all stored events, ordered by `id`, as JSON |

### Planned

| Endpoint | Like you're 5 | Purpose |
|---|---|---|
| `GET /games` | "Tell me about each game and how it's doing" | Aggregated stats per game |
| `GET /players` | "Tell me about each player" | Aggregated stats per player |
| `GET /sessions` (or similar) | "Group these postcards into visits" | Session grouping for a player |
| Analytics endpoints | "What's the completion rate for Level 3?" | Level stats, retention numbers |
| WebSocket endpoint | "Call me the moment something new happens" | Broadcasts new events live to the dashboard |

---

## 7. Development Roadmap

**Like you're 5:** This is the to-do list, in order, so we don't try to build the picture book before the filing cabinet exists.

| # | Milestone | Deliverable | Status |
|---|---|---|---|
| 1 | Foundation | Basic Telemetry Backend (FastAPI + PostgreSQL + `POST`/`GET /events`) | ✅ Complete |
| 2 | Game Integration | Godot SDK Integration | ⏳ Next |
| 3 | Analytics | Analytics Layer (player/level/session stats) | Planned |
| 4 | Dashboard | React Analytics Dashboard | Planned |
| 5 | Scalability | Redis, message queue, workers, rate limiting, auth | Planned |
| 6 | Real-Time / Advanced | WebSockets + session/replay visualization | Planned |
| 7 | Engineering Hardening | Tests, logging, Docker, CI/CD, load testing | Planned |

Full weekly breakdown with calendar deadlines lives in `docs/ROADMAP.md` — this table is just the map; that file is the turn-by-turn directions.

---

## 8. Security & Configuration

**Like you're 5:** Some information — like passwords — should never be written somewhere strangers can see it. And when someone hands you a form to fill in a filing cabinet, you should never let them write directly into the cabinet's instructions, or a sneaky person could trick it into doing something bad.

- **Secrets live in `.env`** (e.g. `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`), loaded via `python-dotenv` — never hardcoded in source files.
- **`.gitignore` excludes** `venv/`, `__pycache__/`, `*.pyc`, and `.env` — so secrets and clutter never get pushed to GitHub.
- **Parameterized SQL queries** are used for all inserts — this prevents SQL injection, which is what happens when someone sneaks extra database commands inside a normal-looking piece of text.
- **Planned:** API key authentication (each game gets its own key, like a house key that only opens one door) and rate limiting (a bouncer who won't let one person flood the door with a thousand postcards a second).

---

## 9. Risks & Watchouts

**Like you're 5:** Things that are easy to trip over later, flagged now so nobody's surprised.

- **Async pitfalls** — Godot's `HTTPRequest` node doesn't hand you an answer right away; it tells you *later*, through a signal, like a text message instead of a phone call you wait on. Redis-based workers have a similar "don't wait around, I'll let you know" behavior. Both are common places for confusion the first time.
- **Session definition is fuzzy** — there's no single "correct" way to decide when one visit ends and another begins. The plan is a simple rule (e.g., a 30-minute gap = a new session) rather than chasing a perfect definition.
- **CORS issues are near-guaranteed** once the React dashboard starts talking to FastAPI — different origins (the dashboard's URL vs. the API's URL) need explicit permission to talk to each other, or the browser blocks it.
- **Scope creep** — the biggest risk on a long solo project isn't difficulty, it's "just one more feature" derailing the current phase. New ideas go in `docs/BACKLOG.md`, not into the current milestone.
- **Silent failures in async systems** — once events flow through a queue instead of straight into the database, a dropped event won't throw an error in your face; it'll just quietly not show up. Logging needs to exist *before* it's needed.

---

## 10. Definition of Done (per phase)

**Like you're 5:** A phase isn't "done" just because it mostly works — it's done when every box on its checklist is actually checked, the same way Milestone 1 was.

Milestone 1's checklist, kept here as the template every future milestone follows:

- [x] Backend server starts
- [x] FastAPI root endpoint works
- [x] PostgreSQL is running
- [x] `questmetrix` database exists
- [x] `events` table exists
- [x] Event format defined
- [x] FastAPI validates event data
- [x] `POST /events` accepts events
- [x] Events are inserted into PostgreSQL
- [x] `GET /events` retrieves stored events
- [x] Multiple events can be stored and retrieved

**Rule for every future milestone:** it isn't closed until its equivalent checklist is fully checked, and the README's "Implemented vs. Planned" section is updated to match reality — never claim a feature is done before it actually is.

---

## 11. Glossary (plain-English cheat sheet)

| Term | Like you're 5 |
|---|---|
| API | A menu of things you're allowed to ask a program to do |
| Endpoint | One specific item on that menu (e.g., `POST /events`) |
| Backend | The kitchen — where the real work happens, out of sight |
| Frontend | The dining room — what the customer actually sees (the dashboard) |
| Database | The filing cabinet that remembers everything |
| SDK | A pre-built toolkit that lets a game "speak" to QuestMetrix without reinventing the wheel |
| Queue | A waiting line, first-come-first-served |
| Cache | A sticky note for something you'll need again soon, so you don't have to look it up from scratch |
| Container (Docker) | A sealed lunchbox with everything needed already packed inside |
| CI/CD | A robot that checks and ships your homework automatically |
