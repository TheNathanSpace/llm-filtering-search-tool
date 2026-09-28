# ---- Front-end: production build ----
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./

RUN npm run build


# ---- Front-end: Compose `dev` profile (hot reload) ----
FROM node:20-alpine AS frontend-dev

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

# Source is bind-mounted at runtime; node_modules is kept via a named volume.
ENV HOSTNAME=0.0.0.0
ENV FRONTEND_PORT=3030

EXPOSE 3030

CMD ["sh", "-c", "exec npx next dev -H 0.0.0.0 -p \"${FRONTEND_PORT:-3030}\""]


# ---- Back-end: install for production image ----
FROM python:3.12-slim AS backend-builder

WORKDIR /build

COPY backend/ ./backend/
RUN pip install --no-cache-dir --prefix=/install ./backend


# ---- Back-end: Compose `dev` profile (uvicorn --reload) ----
FROM python:3.12-slim AS backend-dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/ ./backend/
RUN pip install --no-cache-dir -e ./backend

ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=8000
ENV WATCHFILES_FORCE_POLLING=true

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn llm_rankings.api:app --reload --reload-dir /app/backend --host \"${BACKEND_HOST:-0.0.0.0}\" --port \"${BACKEND_PORT:-8000}\" --env-file /app/.env"]


# ---- Production runtime: API + Next via supervisord ----
FROM python:3.12-slim

# Install supervisord and Node.js runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed llm-rankings package and its dependencies
COPY --from=backend-builder /install /usr/local

# Copy Next.js standalone build
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend/
COPY --from=frontend-builder /app/frontend/.next/static ./frontend/.next/static
COPY --from=frontend-builder /app/frontend/public ./frontend/public

# Supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Defaults for supervisord: uvicorn on BACKEND_HOST:BACKEND_PORT; Next.js uses
# FRONTEND_PORT (exported as PORT for the standalone server).
# Override at runtime with -e. EXPOSE below is build-time metadata only (always
# 3030); it does not follow -e FRONTEND_PORT. Publish with -p host:container where
# the container side matches the runtime listen port, e.g.:
#   docker run -e FRONTEND_PORT=4000 -p 4000:4000 ...
#   docker run -p 3030:3030 ...   # default FRONTEND_PORT
ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=8000
ENV FRONTEND_PORT=3030

EXPOSE 3030

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
