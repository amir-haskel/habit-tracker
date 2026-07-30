# Build context is the REPO ROOT (see docker-compose.yml).
FROM python:3.12-slim

WORKDIR /app

COPY libs/events /app/libs/events
RUN pip install --no-cache-dir "./libs/events[rabbitmq]"

COPY services/notifications /app/services/notifications
RUN pip install --no-cache-dir "./services/notifications[postgres]"

# The API process starts an embedded consumer thread when EVENT_BUS=rabbitmq.
# DATABASE_URL / RABBITMQ_URL are provided by docker-compose.
ENV EVENT_BUS=rabbitmq
EXPOSE 8000

CMD ["uvicorn", "notifications.main:app", "--host", "0.0.0.0", "--port", "8000"]
