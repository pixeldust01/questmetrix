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

Client / API Request -> FastAPI -> PostgreSQL -> events table

Currently, gameplay events can be submitted through the API and
stored in PostgreSQL. Stored events can also be retrieved through
the API.

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

### Planned

- Godot / GDScript SDK
- React
- Redis
- Message Queue
- WebSockets
- Docker
- Automated testing
- CI/CD
- Load testing

## Project Structure

```text
questmetrix/
│
├── backend/
│   ├── main.py
│   ├── event_schema.json
│   ├── requirements.txt
│   ├── .env
│   └── venv/
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

Create a `.env` file inside the `backend/` directory:

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

## Features

### Currently Implemented

- FastAPI backend
- PostgreSQL database
- Telemetry event schema
- `POST /events` endpoint
- `GET /events` endpoint
- Event validation using Pydantic
- Persistent storage of telemetry events
- Interactive API documentation through FastAPI
- Environment-based database configuration

### Planned

- Godot SDK
- Automatic gameplay event collection
- React analytics dashboard
- Gameplay analytics and metrics
- Player/session analysis
- API authentication and API keys
- Redis caching
- Asynchronous event processing
- Message queue integration
- Real-time dashboard updates
- API rate limiting
- Logging and monitoring
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

- [ ] Create QuestMetrix Godot SDK
- [ ] Implement `track()` function
- [ ] Connect Godot SDK to the backend
- [ ] Send gameplay events from a test game

### Phase 3 - Analytics

- [ ] Implement basic gameplay metrics
- [ ] Add player statistics
- [ ] Add level progression analysis
- [ ] Add session analysis

### Phase 4 - Dashboard

- [ ] Build React dashboard
- [ ] Display raw events
- [ ] Display gameplay metrics
- [ ] Add charts and visualizations

### Phase 5 - Scalable Architecture

- [ ] Add Redis caching
- [ ] Add asynchronous event processing
- [ ] Add message queue
- [ ] Add background workers
- [ ] Add API rate limiting
- [ ] Add authentication and API keys

### Phase 6 - Production Engineering

- [ ] Add automated tests
- [ ] Add logging and monitoring
- [ ] Add Docker support
- [ ] Add CI/CD
- [ ] Perform load testing
- [ ] Document system architecture

## Testing

The current implementation is tested manually using the interactive
FastAPI documentation.

Current test flow:

1. Send a telemetry event using `POST /events`.
2. Verify that the API accepts and validates the event.
3. Verify that the event is stored in PostgreSQL.
4. Retrieve stored events using `GET /events`.
5. Verify the returned data against the database.

Automated unit, integration, and load tests will be added as the
project develops.

## License

This project is licensed under the MIT License.
