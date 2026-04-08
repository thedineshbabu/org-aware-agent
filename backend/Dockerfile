FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Run Alembic migrations then start the server
CMD ["sh", "-c", "alembic -c app/db/migrations/alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
