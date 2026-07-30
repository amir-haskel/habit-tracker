# Build context is the REPO ROOT (see docker-compose.yml).
FROM python:3.12-slim

WORKDIR /app

COPY libs/events /app/libs/events
RUN pip install --no-cache-dir "./libs/events[rabbitmq]"

COPY services/notifications /app/services/notifications
RUN pip install --no-cache-dir ./services/notifications

# The API process starts an embedded consumer thread when EVENT_BUS=rabbitmq.
ENV DATABASE_URL=sqlite:////data/notifications.db \
    EVENT_BUS=rabbitmq
VOLUME ["/data"]
EXPOSE 8000

CMD ["uvicorn", "notifications.main:app", "--host", "0.0.0.0", "--port", "8000"]
