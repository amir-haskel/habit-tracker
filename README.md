# Habit Tracker

A habit-tracking app, built as a learning project and structured as microservices
behind an nginx gateway. Backends are Python/FastAPI; the frontend is a React +
Vite SPA. Datastores are SQLite for now (one per service), to be swapped for
PostgreSQL later.

## Architecture

```mermaid
flowchart LR
    Browser["Browser (React SPA)"]
    subgraph Gateway["nginx gateway"]
        direction TB
        SPA["serves built SPA"]
        Proxy["reverse proxy /api/*"]
    end
    HC["habit-core\n(FastAPI + SQLite)"]
    NO["notifications\n(FastAPI + SQLite)"]
    MQ(["RabbitMQ\nhabits.events (topic)"])

    Browser -->|HTTP| Gateway
    Proxy -->|/api/habits → /habits| HC
    Proxy -->|/api/notifications → /notifications| NO
    HC -->|publish domain events| MQ
    MQ -->|habit.created / habit.archived / streak.milestone| NO
```

**Two communication axes:**

- **Synchronous (HTTP)** — the browser and any request/response that needs an
  immediate answer. All client traffic is same-origin `/api/*` through nginx,
  so there's no CORS.
- **Asynchronous (events over RabbitMQ)** — cross-service reactions. habit-core
  *publishes facts* (`habit.logged`, `streak.milestone`, …) to a topic exchange
  and never calls other services directly. notifications *subscribes* and reacts.
  This keeps the services decoupled: notifications can be down and events simply
  buffer in its durable queue.

The broker is hidden behind an `EventBus` interface (`libs/events`), so it's a
swappable detail — `InMemoryEventBus` for tests/local, RabbitMQ in compose, and
(later) SNS/SQS or MSK on AWS — without touching business logic.

## Layout

```
libs/events/            Shared domain-event contracts + EventBus (InMemory + RabbitMQ)
services/
  habit-core/           Habits, logs, streaks, stats. Publishes domain events.
  notifications/        Consumes events; owns its store + REST API. Keeps a local
                        read-model of habits (event-carried state) so it can render
                        habit names without calling habit-core.
frontend/               React + Vite + Tailwind SPA (see frontend/README.md)
deploy/                 nginx.conf, per-image Dockerfiles wiring, docker-compose.yml
tests/integration/      Cross-service event-contract test (in-process, no broker)
```

## Domain events

| Event | Published by | Consumed by | Effect |
|---|---|---|---|
| `habit.created` | habit-core | notifications | Build read-model entry + "now tracking" notification |
| `habit.archived` | habit-core | notifications | Mark read-model entry archived |
| `habit.logged` | habit-core | *(none yet)* | Carries `goal_met`; reserved for future reminder logic |
| `streak.milestone` | habit-core | notifications | Congratulatory notification at 7/14/30/… day streaks |

Contracts live in [`libs/events`](libs/events/src/habit_events/events.py) — both
producer and consumer import them, so the wire format is a single reviewable source.

## Running

### Full stack (docker-compose)

```bash
docker compose -f deploy/docker-compose.yml up --build
# open http://localhost:8080   (RabbitMQ UI at http://localhost:15672, guest/guest)
```

### Locally without Docker

Each service is an independent Python package. Install into one virtualenv for
development:

```bash
python -m venv .venv && . .venv/Scripts/activate    # (.venv/bin/activate on *nix)
pip install -e "libs/events[rabbitmq]" \
            -e "services/habit-core[dev]" \
            -e "services/notifications[dev,rabbitmq]"

# habit-core (defaults to the in-memory bus — no broker needed):
uvicorn habit_core.main:app --port 8000 --app-dir services/habit-core/src

# frontend (proxies /api → http://127.0.0.1:8000):
cd frontend && npm install && npm run dev
```

Point services at RabbitMQ with `EVENT_BUS=rabbitmq` and
`RABBITMQ_URL=amqp://guest:guest@localhost:5672/`.

## Testing

```bash
# per package (mirrors per-service CI)
(cd libs/events && pytest)
(cd services/habit-core && pytest)
(cd services/notifications && pytest)
# cross-service event contract (in-process InMemory bus, no broker)
pytest tests/integration
```

## Status / roadmap

- **Now:** habit-core + notifications + gateway; RabbitMQ events; SQLite per service.
- **Design-forward UI not yet in the model:** weekly/`x-per-week` frequency
  ("Day 3/5"), time-of-day, reminders. The `frequency_type`/`frequency_config`
  columns and the `is_scheduled()` abstraction are in place for when these land.
- **Next:** move stores to PostgreSQL; add a time-based reminder scheduler in the
  notifications service (consuming `habit.logged` to suppress reminders once a
  habit is done for the day); AWS deployment (services + managed broker + RDS).
```
