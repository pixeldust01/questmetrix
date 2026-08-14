# QuestMetrix - Game Telemetry & Analytics Platform

## Overview

QuestMetrix is a game telemetry and analytics platform designed to help
game developers collect, store, process, and visualize gameplay data.

The platform will allow games to send gameplay events such as player deaths,
enemy kills, level completions, and item collections to a backend system.
These events can then be used to generate meaningful gameplay analytics.

## Problem

Game developers need gameplay data to understand how players interact
with their games. Important information such as player progression,
deaths, level completion, and session behaviour can be difficult to
collect and analyse without dedicated infrastructure.

QuestMetrix aims to provide a simple developer-focused platform for
collecting gameplay telemetry and turning raw gameplay events into
useful analytics.

## Goals

- Provide an easy-to-use SDK for sending gameplay events from games.
- Provide a backend API for receiving telemetry data.
- Store gameplay events reliably in a database.
- Process raw events into useful gameplay analytics.
- Provide a dashboard for visualizing gameplay data.
- Support multiple games and players.
- Explore scalable backend concepts such as asynchronous processing,
  caching, rate limiting, and real-time updates.

## Architecture

The planned architecture is:

Game -> QuestMetrix SDK -> Event API -> Message Queue -> Processing Engine -> PostgreSQL / Redis -> Analytics Dashboard

### Current Implementation

The current system implements the initial backend pipeline:

Godot SDK -> FastAPI -> PostgreSQL -> events table

Currently, gameplay events can be submitted from a Godot game client,
sent through the API, and stored in PostgreSQL. Stored events can
also be retrieved through the API.

## Tech Stack

### Current

- Python
- FastAPI
- Pydantic
- PostgreSQL
- psycopg2
- python-dotenv
- Git
- GitHub
- Godot / GDScript SDK (partial)
- React

### Planned

- Redis
- Message Queue
- WebSockets
- Docker
- Automated testing
- CI/CD
- Load testing

## Getting Started

### Prerequisites

Install the following:

- Python
- PostgreSQL
- Git

### Backend Setup

Clone the repository:

```bash
git clone <repository-url>
cd questmetrix
```

Create and activate a Python virtual environment:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside the `backend/` directory with your private PostgreSQL credentials:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=questmetrix
DB_USER=postgres
DB_PASSWORD=your_postgresql_password
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

### Frontend Setup

Install the dependencies from the dashboard directory `/dashboard`:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The dashboard is available at `http://localhost:5173`.

### Godot Client Setup

For instructions on setting up the Godot test client, please refer to the SDK's documentation in `sdk/README.md`.

## Features

### Currently Implemented

- FastAPI backend
- PostgreSQL database
- Telemetry event schema
- `POST /events`
- `GET /events`
- Event validation using Pydantic
- Persistent telemetry storage
- Godot telemetry SDK (partial)
- Godot → FastAPI event submission
- SDK error handling for unreachable backend
- Analytics endpoints to retrieve aggregated game, player, and level data
- Session and retention analysis
- React analytics dashboard

### Planned

- Redis caching
- Asynchronous event processing
- Message queue
- Background workers
- API authentication
- API rate limiting
- WebSockets
- Session/replay analysis
- Docker
- CI/CD
- Load testing

## Roadmap

### Phase 1 - Backend Foundation

- [x] Set up project repository
- [x] Set up FastAPI backend
- [x] Define initial telemetry event schema
- [x] Set up PostgreSQL
- [x] Create events table
- [x] Implement `POST /events`
- [x] Implement `GET /events`

### Phase 2 - Game SDK

- [x] Create QuestMetrix Godot SDK
- [x] Implement `track()` function
- [x] Connect Godot SDK to the backend
- [x] Send gameplay events from a test game

### Phase 3 - Analytics

- [x] Implement basic gameplay metrics
- [x] Add player statistics
- [x] Add level progression analysis
- [x] Add session analysis

### Phase 4 - Dashboard

- [x] Build React dashboard
- [x] Display raw events
- [x] Display gameplay metrics
- [x] Add charts and visualizations

### Phase 5 - Scalable Infrastructure

- [ ] Add Redis caching
- [ ] Add asynchronous event processing
- [ ] Add message queue
- [ ] Add background workers
- [ ] Add API rate limiting
- [ ] Add authentication and API keys

### Phase 6 - Real-Time + Session Replay

- [ ] Add WebSockets
- [ ] Add session/replay analysis

### Phase 7 - Engineering Hardening

- [ ] Add automated tests
- [ ] Add logging and monitoring
- [ ] Add Docker support
- [ ] Add CI/CD
- [ ] Perform load testing
- [ ] Document system architecture

## Testing

Run automated backend tests have been added using this `pytest` command from directory `backend/`:

```bash
python -m pytest
```

Current test flow:

1. Run the FastAPI backend server.
2. Run the Godot test project.
3. Trigger an event in the game to call `QuestMetrix.track()`.
4. Verify that the API server logs a successful `POST /events` request.
5. Verify that the event is stored correctly in the PostgreSQL `events` table.
6. Optionally, use the `GET /events` endpoint to retrieve stored events and verify the data.

Further unit, integration, and load tests will be added as the project develops.

## License

This project is licensed under the MIT License.
