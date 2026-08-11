# Technical Design Document (TDD): QuestMetrix

**Version:** v0.1
**Date:** 10 Aug 2026
**Status:** Living document — update as milestones close

---

## 1. Overview

**Executive Summary:** QuestMetrix is a telemetry and analytics platform designed for game developers. It provides the infrastructure to receive, store, process, and visualize gameplay events. The platform's core function is to aggregate event data from games and transform it into actionable insights through an analytics dashboard.

The end-to-end event data flow is as follows:

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

The current implementation covers the core API and database components. The system is being developed iteratively, with each new component building upon a stable foundation.

---

## 2. Goals & Scope

**Development Philosophy:** The project follows an iterative development model. The initial milestone focused on establishing a foundational, end-to-end event pipeline. Subsequent milestones will incrementally build upon this core by adding components for data ingestion, analytics, visualization, and scalability.

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

**High-level description:** The current architecture is a monolithic backend service. It exposes a REST API for event ingestion. Incoming data is validated against a Pydantic model and then persisted directly to a PostgreSQL database. Clients currently interact with the API via the auto-generated Swagger UI for manual testing and validation.

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

**High-level description:** The target architecture is a distributed, scalable system designed for high-throughput event processing. It decouples the API from the database using a message queue, allowing for asynchronous processing and improved resilience. A caching layer (Redis) will be introduced for frequently accessed data and real-time analytics. The frontend will be a standalone React application that communicates with the backend via the API and WebSockets for live data updates.

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

**Architectural Principle:** The system is being built iteratively. Each component in the target architecture will be implemented and integrated sequentially to ensure stability and a thorough understanding of each part of the system before adding the next. This phased approach mitigates the risks associated with a "big bang" implementation.

---

## 4. Technology Stack

**Guiding Principle:** Each technology is chosen for a specific role, favoring mature, well-supported tools to ensure stability and maintainability.

### Currently used

| Component       | Technology                   | Role                                                      |
| --------------- | ---------------------------- | --------------------------------------------------------- |
| Language        | Python                       | Backend programming language                              |
| API framework   | FastAPI                      | Handles HTTP requests/responses and routing               |
| Validation      | Pydantic                     | Enforces data contracts and validates incoming payloads   |
| Database        | PostgreSQL 18                | Persistent storage for event data                         |
| DB driver       | psycopg2-binary              | PostgreSQL adapter for Python                             |
| Config loader   | python-dotenv                | Manages environment variables for configuration           |
| API testing     | FastAPI Swagger/OpenAPI docs | Interactive API documentation and manual endpoint testing |
| Version control | Git                          | Source code management and version tracking               |
| Remote repo     | GitHub                       | Hosted Git repository and collaboration platform          |

### Planned

| Component         | Planned technology                | Role                                                                        |
| ----------------- | --------------------------------- | --------------------------------------------------------------------------- |
| Game SDK          | Godot / GDScript                  | Provides a client library for game engines to send telemetry data           |
| Dashboard         | React                             | Frontend framework for building the user-facing analytics dashboard         |
| Cache             | Redis                             | In-memory data store for caching, session management, and real-time metrics |
| Async processing  | Message queue + workers           | Decouples event ingestion from processing to handle high-throughput loads   |
| Real-time updates | WebSockets                        | Enables bidirectional communication for live updates on the dashboard       |
| Containerization  | Docker                            | Standardizes development and deployment environments                        |
| CI/CD             | GitHub Actions (or similar)       | Automates testing, building, and deployment workflows                       |
| Testing           | Unit + integration + load testing | Ensures code quality, system stability, and performance under load          |

---

## 5. Data Model

### 5.1 Event schema (implemented)

**Description:** The `Event` model is a Pydantic `BaseModel` that defines the data contract for all incoming telemetry events. It ensures that every event processed by the API conforms to a standardized structure, enforcing type and presence constraints.

```python
class Event(BaseModel):
    event: str        # The name of the event that occurred (e.g., "enemy_killed").
    player_id: str     # A unique identifier for the player.
    game_id: str        # A unique identifier for the game.
    timestamp: str        # An ISO 8601 timestamp indicating when the event occurred.
    level: int              # The game level in which the event occurred.
```

Sample payload:

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

**Description:** The `events` table in the PostgreSQL database is the persistent store for validated telemetry data. Its schema mirrors the `Event` model, with an added `id` column as the primary key.

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

| Column      | Description                                             |
| ----------- | ------------------------------------------------------- |
| `id`        | A unique, auto-incrementing identifier for the record.  |
| `event`     | The name of the event.                                  |
| `player_id` | The identifier of the player associated with the event. |
| `game_id`   | The identifier of the game that sent the event.         |
| `timestamp` | The timestamp of the event occurrence.                  |
| `level`     | The game level where the event occurred.                |

The `NOT NULL` constraints ensure data integrity by requiring all fields to be present for every record.

### 5.3 Planned data model extensions

- **Sessions** — grouping a player's events that happen close together in time into one "play session" (like grouping all the postcards someone mailed during one visit to the post office).
- **Retention** — tracking whether a player came back and mailed more postcards on a later day (did they visit the game again?).
- **Replay** — keeping the _order_ of a player's events, so instead of a pile of postcards you get a story: START LEVEL → MOVE → COLLECT ITEM → FIGHT ENEMY → LOSE HP → DIE.

---

## 6. API Endpoints

### Implemented

| Method | Endpoint  | Description                                                    |
| ------ | --------- | -------------------------------------------------------------- |
| `GET`  | `/`       | Health check endpoint to confirm service availability.         |
| `POST` | `/events` | Ingests and persists a single gameplay event after validation. |
| `GET`  | `/events` | Retrieves all stored events, ordered by `id`.                  |

### Planned

| Method      | Endpoint       | Description                                                              |
| ----------- | -------------- | ------------------------------------------------------------------------ |
| `GET`       | `/games`       | Provides aggregated statistics for each game.                            |
| `GET`       | `/players`     | Provides aggregated statistics for each player.                          |
| `GET`       | `/sessions`    | Retrieves events grouped by player session.                              |
| `GET`       | `/analytics/*` | A collection of endpoints for specific metrics (e.g., completion rates). |
| `WEBSOCKET` | `/ws`          | Establishes a WebSocket connection for real-time event broadcasting.     |

---

## 7. Development Roadmap

**Overview:** The project is developed in distinct phases, or milestones. This ensures a modular and incremental build-out, where each new component is added to a stable, well-understood foundation.

| #   | Milestone             | Deliverable                                                           | Status      |
| --- | --------------------- | --------------------------------------------------------------------- | ----------- |
| 1   | Foundation            | Basic Telemetry Backend (FastAPI + PostgreSQL + `POST`/`GET /events`) | ✅ Complete |
| 2   | Game Integration      | Godot SDK Integration                                                 | ⏳ Next     |
| 3   | Analytics             | Analytics Layer (player/level/session stats)                          | Planned     |
| 4   | Dashboard             | React Analytics Dashboard                                             | Planned     |
| 5   | Scalability           | Redis, message queue, workers, rate limiting, auth                    | Planned     |
| 6   | Real-Time / Advanced  | WebSockets + session/replay visualization                             | Planned     |
| 7   | Engineering Hardening | Tests, logging, Docker, CI/CD, load testing                           | Planned     |

A detailed breakdown of tasks and deadlines is maintained in `docs/ROADMAP.md`.

---

## 8. Security & Configuration

**Guiding Principles:** Security is addressed through a combination of secret management, input validation, and secure coding practices. The configuration is designed to be portable and environment-agnostic.

- **Secret Management:** All sensitive data (e.g., database credentials) is stored in a `.env` file and loaded into the application environment at runtime using `python-dotenv`. This file is explicitly excluded from version control.
- **`.gitignore`:** The `.gitignore` file prevents secrets, environment-specific files (`venv/`), and compiled artifacts (`__pycache__/`, `*.pyc`) from being committed to the repository.
- **SQL Injection Prevention:** The use of parameterized queries is enforced by the database driver (`psycopg2`), which automatically escapes inputs and prevents SQL injection vulnerabilities.
- **Planned Security Measures:** Future milestones will introduce API key authentication to secure endpoints and rate limiting to prevent abuse and ensure service stability.

---

## 9. Risks & Watchouts

**Overview:** This section documents potential technical challenges and project risks to ensure they are anticipated and mitigated.

- **Asynchronous Programming Complexity:** The introduction of asynchronous components (e.g., Godot's `HTTPRequest` signals, Redis-based workers) requires careful management of state and control flow to avoid race conditions and other common pitfalls.
- **Session Heuristics:** Defining a "session" is inherently ambiguous. The initial implementation will use a simple time-based heuristic (e.g., a 30-minute inactivity gap constitutes a new session) to avoid over-engineering.
- **CORS Configuration:** Cross-Origin Resource Sharing (CORS) issues are expected when integrating the React frontend with the FastAPI backend, as they will be served from different origins. The backend will require explicit CORS configuration to allow requests from the frontend's domain.
- **Scope Creep:** The primary project management risk is the temptation to add features outside the current milestone's scope. A backlog (`docs/BACKLOG.md`) is maintained to capture new ideas without disrupting the roadmap.
- **Silent Failures in Distributed Systems:** In an asynchronous, distributed architecture, failures may not be immediately apparent. Comprehensive logging and monitoring are critical to ensure that event processing failures are detected and can be debugged.

---

## 10. Definition of Done (per phase)

**Standard:** A milestone is considered "done" only when all functional and non-functional requirements have been met and verified. This includes updating project documentation to reflect the new state of the system.

The checklist for Milestone 1 serves as the template for all subsequent milestones:

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

**Rule:** A milestone is not closed until its corresponding checklist is complete and the README has been updated to accurately represent the implemented features.

---

## 11. Glossary

| Term               | Definition                                                                                                                  |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| API                | An Application Programming Interface; a set of rules and definitions for building and interacting with software components. |
| Endpoint           | A specific URL where an API can be accessed to perform a particular function (e.g., `POST /events`).                        |
| Backend            | The server-side components of an application, responsible for logic, data processing, and storage.                          |
| Frontend           | The client-side components of an application that the user interacts with directly (e.g., the dashboard).                   |
| Database           | An organized collection of data, structured for efficient storage and retrieval.                                            |
| SDK                | A Software Development Kit; a set of tools and libraries that simplify development for a specific platform.                 |
| Queue              | A data structure that manages a list of items in a first-in, first-out (FIFO) manner.                                       |
| Cache              | A high-speed data storage layer used to store a subset of transient data for faster access.                                 |
| Container (Docker) | A lightweight, standalone, executable package of software that includes everything needed to run it.                        |
| CI/CD              | Continuous Integration/Continuous Deployment; a set of practices for automating the software development lifecycle.         |
