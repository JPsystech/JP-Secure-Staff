# JP Secure Staff Backend - Production (Railway / Docker)
# Root context MUST be backend/ so COPY . . brings app/, alembic/, start.sh, etc.
FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg2-binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Remove any .env so we never bake secrets into image
RUN find . -name ".env" -delete 2>/dev/null || true
RUN chmod +x start.sh

# Railway sets PORT at container start; default for local runs
ENV PORT=8000
EXPOSE 8000

# Shell form so the process gets Railway's env (including PORT).
# start.sh validates PORT and runs alembic then uvicorn.
CMD ["/bin/bash", "-c", "./start.sh"]
