FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1

# Dépendances (couche mise en cache)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Code + restauration de la base pendant la construction de l'image
COPY . .
RUN .venv/bin/python -c "from main import preparer_base; preparer_base()"

ENV PORT=8080
CMD exec .venv/bin/gunicorn wsgi:server --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120