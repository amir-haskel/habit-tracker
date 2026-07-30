# Build context is the REPO ROOT (see docker-compose.yml) so we can pull in the
# shared libs/events package alongside the service.
FROM python:3.12-slim

WORKDIR /app

# Shared event contracts + adapters first (habit-core depends on it).
COPY libs/events /app/libs/events
RUN pip install --no-cache-dir "./libs/events[rabbitmq]"

COPY services/habit-core /app/services/habit-core
RUN pip install --no-cache-dir ./services/habit-core

# Store the SQLite DB on a mounted volume, run against the broker.
ENV DATABASE_URL=sqlite:////data/habit_core.db \
    EVENT_BUS=rabbitmq
VOLUME ["/data"]
EXPOSE 8000

CMD ["uvicorn", "habit_core.main:app", "--host", "0.0.0.0", "--port", "8000"]
