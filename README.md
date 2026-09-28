# Moh Maya

A life-simulation foundation: a persistent world in PostgreSQL, a FastAPI developer API, and a pause-between-decisions simulation engine.

The first milestone is not a playable game UI. It proves that a world exists independently of HTTP, advances only when a player decision is applied, persists authoritative state in PostgreSQL, and can be inspected afterward.

These endpoints are a **developer/God inspect** surface. They can show hidden world information. They are not the player experience and do not filter by player perception.

## What you need

- Python 3.11+ already installed
- Docker Desktop (or another Docker engine) so PostgreSQL can run locally
- PostgreSQL does **not** need to be installed on the host

## 1. Create a virtual environment

From the project root (`D:\coding_world\Moh_Maya`):

```powershell
python -m venv .venv
```

## 2. Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again.

## 3. Install requirements

```powershell
pip install -r requirements.txt
```

## 4. Create environment configuration

```powershell
copy .env.example .env
```

`.env` is gitignored. It must exist so Docker Compose and the app can read:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_PORT`
- `DATABASE_URL` (development database `mohmaya`)
- `TEST_DATABASE_URL` (pytest database `mohmaya_test`)

Do not commit `.env` or real secrets. Pytest uses **only** `TEST_DATABASE_URL`. It never writes to `DATABASE_URL`.

## 5. Start PostgreSQL with Docker Compose

```powershell
docker compose up -d
```

Wait until the container is healthy:

```powershell
docker compose ps
```

`mohmaya-postgres` should show `healthy` (or at least be running and accepting connections). A first-time volume also creates `mohmaya_test` on the same Postgres 16 instance. If the volume already existed, pytest creates `mohmaya_test` when it starts.

## 6. Run Alembic migrations

The app never creates tables on startup. Schema comes only from migrations. This upgrades the **development** database:

```powershell
alembic upgrade head
```

Pytest runs `alembic upgrade head` against `mohmaya_test` itself.

## 7. Seed a development world

```powershell
python scripts\seed_world.py
```

This creates **Laketown** at Day 1, 08:00, status `paused`, with locations, people, households, businesses, relationships, and an initial event. Seed data stores human-readable names; simulation logic uses entity IDs. The Cafe UUID is also written to `world.world_state.demo.walk_to_cafe_location_id` so the demo POST body can omit `location_id`.

If Laketown already exists, the script prints its id and exits. To recreate it:

```powershell
python scripts\seed_world.py --reset
```

Copy the printed world id. You will need it for API calls.

## 8. Start FastAPI

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 9. Run tests

In another terminal, with the venv activated and PostgreSQL running:

```powershell
pytest
```

Tests connect only to `mohmaya_test`.

## 10. Inspect the API (God / developer)

PowerShell examples (replace `WORLD_ID`):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/worlds
Invoke-RestMethod http://127.0.0.1:8000/world/WORLD_ID
Invoke-RestMethod http://127.0.0.1:8000/world/WORLD_ID/locations
Invoke-RestMethod http://127.0.0.1:8000/world/WORLD_ID/people
Invoke-RestMethod http://127.0.0.1:8000/world/WORLD_ID/events
Invoke-RestMethod http://127.0.0.1:8000/world/WORLD_ID/relationships
Invoke-RestMethod http://127.0.0.1:8000/world/WORLD_ID/knowledge
Invoke-RestMethod http://127.0.0.1:8000/world/WORLD_ID/memories
Invoke-RestMethod http://127.0.0.1:8000/world/WORLD_ID/graph
```

`GET /worlds`, `GET /world/{id}/knowledge`, and `GET /world/{id}/memories` are God inspect routes. They return authoritative rows, not what a player would know.

## Advance the simulation

Laketown starts paused at Day 1, 08:00. `WALK_TO_CAFE` is a temporary development action with a placeholder cost of 30 game minutes. The engine moves the player to a world-scoped `location_id`. You can send that id explicitly, or omit it and use the seeded demo UUID:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri http://127.0.0.1:8000/world/WORLD_ID/simulation/advance `
  -ContentType "application/json" `
  -Body '{"action_type":"WALK_TO_CAFE"}'
```

Or with an explicit Cafe id from `GET /world/WORLD_ID/locations`:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri http://127.0.0.1:8000/world/WORLD_ID/simulation/advance `
  -ContentType "application/json" `
  -Body '{"action_type":"WALK_TO_CAFE","location_id":"CAFE_LOCATION_ID"}'
```

Or wait an explicit number of minutes:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri http://127.0.0.1:8000/world/WORLD_ID/simulation/advance `
  -ContentType "application/json" `
  -Body '{"action_type":"WAIT","minutes":15}'
```

Then query the world again. Time, locations, states, and events should have changed, and status should be `paused`. The Laketown demo still runs 08:00→08:30: Arjun arrives at the Cafe, Sanjay opens it, Priya completes a morning routine, Meera takes a call, then the world pauses.

## Restart / persistence check

1. Advance the world once and note `current_day`, `current_minute`, and a changed person/event.
2. Stop the FastAPI process (Ctrl+C). Leave PostgreSQL running.
3. Start FastAPI again.
4. `GET /world/{world_id}` — the same clock and state must still be there.

The world does not live in Python memory. PostgreSQL is the source of truth.

## Architecture

```
FastAPI  →  Application services  →  Simulation engine  →  Repositories  →  PostgreSQL
PostgreSQL  →  GraphService (derived view)  →  developer inspect endpoints
```

- The simulation package does not import FastAPI.
- Worlds are isolated by `world_id` on every world-owned table.
- Engine logic references entity IDs, not display names.
- EventEngine materializes due schedules; CharacterEngine acts on those events.
- A simulation advance is one SQLAlchemy transaction. Failure rolls the whole advance back.
- The graph is not a database. It is a JSON view of SQL rows.

## Intentionally not implemented

LLM integration, React UI, GraphDB, microservices, combat, quests, offline/background simulation, locked tick durations, locked resource formulas, and player-facing knowledge filtering.
