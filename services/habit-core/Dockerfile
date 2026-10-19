# Build context is the REPO ROOT (see docker-compose.yml) so we can pull in the
# shared libs/events package alongside the service.
FROM python:3.12-slim

WORKDIR /app

# Shared event contracts + adapters first (habit-core depends on it).
COPY libs/events /app/libs/events
RUN pip install --no-cache-dir "./libs/events[aws]"

COPY services/habit-core /app/services/habit-core
RUN pip install --no-cache-dir "./services/habit-core[postgres]"

# DATABASE_URL / SNS_TOPIC_ARN / AWS_* are provided by docker-compose (locally)
# or the ECS task definition (AWS).
ENV EVENT_BUS=aws
EXPOSE 8000

CMD ["uvicorn", "habit_core.main:app", "--host", "0.0.0.0", "--port", "8000"]
