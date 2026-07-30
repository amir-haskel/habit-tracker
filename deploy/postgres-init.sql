-- Runs once on first Postgres startup (docker-entrypoint-initdb.d).
-- One database per service — each service owns its own schema/data.
CREATE DATABASE habit_core;
CREATE DATABASE notifications;
