FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install deps first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source (respects .dockerignore — no .env, no secrets)
COPY . .

# Default command (overridden per service in docker-compose.yml)
CMD ["python", "-m", "bot.main"]
