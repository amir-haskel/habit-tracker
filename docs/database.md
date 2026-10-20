# Database contract (PostgreSQL / RDS)

This is the contract between the application and the database. The app creates
**no** infrastructure: whoever provisions the environment (Terraform) provides the
RDS instance, the secret and the task wiring below. Locally, PostgreSQL in
[`deploy/docker-compose.yml`](../deploy/docker-compose.yml) plays the same role
(it is initialised by [`deploy/postgres-init.sql`](../deploy/postgres-init.sql)).

## Databases

One database per service on the same instance; each service owns its schema
(tables are created by the service at startup).

| Service | Database | Created by |
|---|---|---|
| habit-core | `habit_core` | RDS itself (the initial database, `db_name`) |
| notifications | `notifications` | the service itself at startup when `CREATE_DATABASE_ON_STARTUP=true` (see below), or the one-off [bootstrap job](#bootstrap-job-notifications-database) |

RDS creates only one initial database, hence one of the two mechanisms above.

### Creating the database at startup (notifications)

Set `CREATE_DATABASE_ON_STARTUP=true` on the notifications service. Before it
creates its tables it connects to the maintenance database `postgres` with its own
`DB_*` credentials and runs `CREATE DATABASE <DB_NAME>` if the database is missing
(safe if several tasks start at once). It requires `DB_HOST`, `DB_NAME`, `DB_USER`
and `DB_PASSWORD`, and a role allowed to create databases (today both services use
the RDS master user, which is). It is off by default, so local runs never do this.
If you later move to per-service database users without that right, switch back to
the bootstrap job.

## Environment variables (both services)

habit-core and notifications read the same variables. Names are case-insensitive.

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | *(unset)* | Full SQLAlchemy URL. **If set, it wins** and the `DB_*` variables are ignored (compose uses this). When nothing is set the service falls back to SQLite (`sqlite:///./habit_core.db` / `./notifications.db`). |
| `DB_HOST` | *(unset)* | Setting this switches on component mode: the URL is built as `postgresql+psycopg://DB_USER:DB_PASSWORD@DB_HOST:DB_PORT/DB_NAME`. |
| `DB_PORT` | `5432` | |
| `DB_NAME` | *(unset)* | `habit_core` for habit-core, `notifications` for notifications. |
| `DB_USER` | *(unset)* | |
| `DB_PASSWORD` | *(unset)* | Special characters are fine; they are URL-escaped when the URL is built. Never logged. |
| `DB_SSLMODE` | *(empty)* | Added to the URL as `?sslmode=...` when non-empty. Use `require` on RDS. |

Precedence: explicit `DATABASE_URL` > components (when `DB_HOST` is set) > SQLite.
If `DB_HOST` is set but `DB_NAME`, `DB_USER` or `DB_PASSWORD` is missing, the
service refuses to start with an error naming the missing variables.

## RDS master secret and ECS injection

With `manage_master_user_password`, RDS keeps the master credentials in AWS
Secrets Manager as JSON with exactly two keys:

```json
{"username": "...", "password": "..."}
```

ECS cannot build a connection string from that, but it can inject a single JSON
key as an environment variable. In the container definition, `secrets` entries use
`valueFrom` = `<secret-arn>:<json-key>::` (the two trailing colons leave the
version stage and version id empty, i.e. the current version):

```json
"secrets": [
  {"name": "DB_USER",     "valueFrom": "<secret-arn>:username::"},
  {"name": "DB_PASSWORD", "valueFrom": "<secret-arn>:password::"}
],
"environment": [
  {"name": "DB_HOST",    "value": "<rds endpoint address>"},
  {"name": "DB_PORT",    "value": "5432"},
  {"name": "DB_NAME",    "value": "habit_core"},
  {"name": "DB_SSLMODE", "value": "require"}
]
```

(`DB_NAME` is `notifications` for the notifications service. `DB_HOST` is the
instance endpoint address, without the port.) The **task execution role** (not the
task role) needs `secretsmanager:GetSecretValue` on the secret, plus `kms:Decrypt`
if the secret uses a customer-managed key. Do not set `DATABASE_URL` on AWS.

Both services currently connect as the RDS master user.

## TLS

RDS PostgreSQL 15+ enforces TLS by default (`rds.force_ssl=1`): connections
without it are rejected. Set `DB_SSLMODE=require` (encrypts, does not verify the
server certificate). Stronger modes (`verify-full`) additionally need the RDS CA
bundle inside the image and `sslrootcert`, which the app does not configure today.
The local compose Postgres has no TLS, so leave `DB_SSLMODE` empty there.

## Bootstrap job (notifications database)

`notifications.bootstrap_db` creates the `notifications` database if it is missing.
It is idempotent (a second run prints that it already exists and changes nothing)
and exits non-zero on any failure.

It connects to the maintenance database `postgres` with the **master**
credentials, so run it once per environment after RDS is up, inside the VPC (RDS
is not publicly reachable): an ECS run-task using the **notifications image**,
the same network configuration as the notifications service (subnets and a
security group allowed to reach RDS on 5432), the same `DB_*` secrets and
environment as above, and this command override:

```
python -m notifications.bootstrap_db
```

| Variable | Default | Meaning |
|---|---|---|
| `DB_HOST`, `DB_USER`, `DB_PASSWORD` | *(required)* | Master credentials (`DB_USER`/`DB_PASSWORD` from the secret as above). |
| `DB_PORT` | `5432` | |
| `DB_SSLMODE` | *(empty)* | `require` on RDS. |
| `BOOTSTRAP_DB_NAME` | `notifications` | Database to create. `DB_NAME` is **not** used. |

Success looks like `bootstrap_db: database 'notifications' created` (or
`already exists`) in the task's logs and exit code 0. Run it before the
notifications service starts; otherwise the service fails to connect and ECS will
keep restarting it until the database exists.

Locally (the compose init script already creates both databases, so this is a
no-op unless you pass a different `BOOTSTRAP_DB_NAME`):

```bash
docker compose -f deploy/docker-compose.yml up -d postgres
DB_HOST=localhost DB_USER=habit DB_PASSWORD=habit \
  python -m notifications.bootstrap_db        # needs: pip install -e "services/notifications[postgres]"
```
