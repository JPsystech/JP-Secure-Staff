# JP Secure Staff - Backend (production). Railway / Docker.
FROM python:3.12-slim

WORKDIR /app

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN find . -name ".env" -delete 2>/dev/null || true
RUN chmod +x start.sh

ENV PORT=8000
EXPOSE 8000

CMD ["bash", "./start.sh"]
