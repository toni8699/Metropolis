FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend package
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY db/ ./db/

WORKDIR /app/backend

EXPOSE 5000

CMD ["uvicorn", "vroom.asgi:app", "--host", "0.0.0.0", "--port", "5000"]
