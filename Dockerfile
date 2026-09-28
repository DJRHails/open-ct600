# Build the React frontend.
FROM node:22.22-alpine AS frontend
WORKDIR /frontend
RUN npm install --global pnpm@12.6.0
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

# Serve the API and the built frontend from one FastAPI process.
FROM python:3.13.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.18 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock backend/.python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/src ./src
RUN uv sync --frozen --no-dev
COPY --from=frontend /frontend/dist ./static

RUN useradd --system --uid 10001 app
USER app
ENV PATH="/app/.venv/bin:$PATH" STATIC_DIR=/app/static
EXPOSE 8000
CMD ["uvicorn", "--factory", "open_ct600.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
