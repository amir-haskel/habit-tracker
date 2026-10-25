# Gateway image: builds the Vite SPA, then serves it via nginx and proxies /api.
# Build context is the REPO ROOT (see docker-compose.yml).

FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
# The official image renders /etc/nginx/templates/*.template with envsubst at
# start and writes the result to /etc/nginx/conf.d/. The filter is a regex
# matched against variable NAMES (unanchored, hence ^...$): only these three are
# substituted, so nginx's own $variables in the template survive.
COPY deploy/nginx.conf.template /etc/nginx/templates/default.conf.template
ENV DNS_RESOLVER=127.0.0.11
ENV HABIT_CORE_UPSTREAM=habit-core:8000
ENV NOTIFICATIONS_UPSTREAM=notifications:8000
ENV NGINX_ENVSUBST_FILTER='^(DNS_RESOLVER|HABIT_CORE_UPSTREAM|NOTIFICATIONS_UPSTREAM)$'
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
