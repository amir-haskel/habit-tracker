# Gateway (nginx)

The gateway is the only public entry point of the app. One container, built from
[`deploy/Dockerfile`](../deploy/Dockerfile), does two jobs:

- serves the built Vite SPA (static files, SPA fallback for deep links such as `/habit/3`);
- reverse-proxies API calls, same-origin so the browser needs no CORS:

| Browser path | Forwarded to | Upstream path |
|---|---|---|
| `/api/notifications[/...]` | notifications | `/notifications[/...]` |
| `/api/<anything else>` | habit-core | `/<anything else>` |

The `/api` prefix is stripped, and query strings are passed through.

It listens on **port 80**.

## Configuration

The same image runs locally and on AWS. The nginx config is a template
([`deploy/nginx.conf.template`](../deploy/nginx.conf.template)); the official
nginx image fills it in with `envsubst` when the container starts. Only the
three variables below are substituted (`NGINX_ENVSUBST_FILTER` in the
Dockerfile), so nginx's own `$host`, `$uri`, ... are left alone.

| Variable | Meaning | Local default (docker-compose) | AWS example (ECS + Cloud Map) |
|---|---|---|---|
| `DNS_RESOLVER` | DNS server nginx asks at request time | `127.0.0.11` (Docker's embedded DNS) | `10.0.0.2` (VPC resolver: VPC CIDR base + 2) |
| `HABIT_CORE_UPSTREAM` | habit-core as `host:port` | `habit-core:8000` | `habit-core.habit.local:8000` |
| `NOTIFICATIONS_UPSTREAM` | notifications as `host:port` | `notifications:8000` | `notifications.habit.local:8000` |

The defaults are baked into the image, so docker-compose works without setting
anything (the compose file repeats them as documentation). On ECS, set the three
as container environment variables in the task definition.

Names are re-resolved at request time (`valid=10s`), not once at startup, so
the gateway follows tasks that restart and get a new IP. It also means nginx
starts fine even if an upstream does not exist yet.

## Health check: `/healthz`

`GET /healthz` returns `200` with body `ok`. It is answered by nginx itself:
never proxied, not logged, and independent of habit-core and notifications. Use
it as the health check path of the ALB target group (`/healthz`, port 80,
success code `200`).

Because it ignores the upstreams, a healthy gateway does not mean the API
works: an unreachable upstream shows up as `502` on `/api/...`, not as a failed
health check.

## Networking requirements

The gateway needs **outbound** access to its upstreams:

- to the habit-core and notifications tasks on port 8000 (their security groups
  must allow inbound 8000 from the gateway's security group);
- to the DNS resolver on port 53 (UDP and TCP) -- the VPC resolver is
  reachable from inside the VPC by default.

Inbound, it only needs port 80 from the load balancer.

## Try it locally

```
docker compose -f deploy/docker-compose.yml up --build
curl http://localhost:8080/healthz
```

Render the config with other values (prints the effective nginx config):

```
docker run --rm -e DNS_RESOLVER=10.0.0.2 \
  -e HABIT_CORE_UPSTREAM=habit-core.habit.local:8000 \
  -e NOTIFICATIONS_UPSTREAM=notifications.habit.local:8000 \
  habit-gateway nginx -T
```
