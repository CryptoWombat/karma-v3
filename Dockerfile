# Karma Platform v3 API
FROM python:3.12-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY app/ app/
COPY static/ static/
COPY alembic/ alembic/
COPY alembic.ini .

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Migrate (Postgres) then start; alembic may fail on SQLite
CMD ["sh", "-c", "python -m alembic upgrade head 2>/dev/null; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
