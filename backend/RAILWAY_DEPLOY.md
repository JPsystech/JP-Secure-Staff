# Railway Deployment – Backend (FastAPI)

One production-ready setup so the app deploys on first retry.

---

## 1. Solution choice: **Dockerfile-based**

**Why Dockerfile (not Nixpacks/Procfile only):**

- **PORT:** Railway injects `PORT` at **container start**. With Dockerfile we control the process (bash → start.sh → uvicorn) so the same process tree gets `PORT`. Nixpacks can sometimes run a different shell or layer and lose env.
- **Reproducibility:** Same image locally and on Railway.
- **Dependencies:** `psycopg2-binary`, `email-validator`, system libs (libpq) are fixed in the image.
- **Working directory:** `WORKDIR /app` and `COPY . .` from **backend/** guarantee `app/`, `alembic/`, `start.sh` are in `/app`; no `cd backend` or path confusion.

---

## 2. Final files

### Dockerfile (backend/Dockerfile)

```dockerfile
# JP Secure Staff Backend - Production (Railway / Docker)
# Root context MUST be backend/ so COPY . . brings app/, alembic/, start.sh, etc.
FROM python:3.12-slim

WORKDIR /app

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

CMD ["/bin/bash", "-c", "./start.sh"]
```

### start.sh (backend/start.sh)

- Uses **bash** so `${PORT}` and regex work.
- **Validates PORT:** if unset or not a number, uses 8000 (avoids “$PORT is not a valid integer”).
- **exec uvicorn** so uvicorn is PID 1 and gets signals correctly.

```bash
#!/usr/bin/env bash
set -e

PORT_NUM=8000
if [[ -n "${PORT}" ]] && [[ "${PORT}" =~ ^[0-9]+$ ]]; then
  PORT_NUM="${PORT}"
fi

echo "Running migrations..."
alembic upgrade head

echo "Starting uvicorn on 0.0.0.0:${PORT_NUM}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT_NUM}"
```

### requirements.txt changes

- **pydantic[email]** – for `EmailStr` in schemas (auth, user, person).
- **email-validator>=2.0.0** – explicit so EmailStr works even if pydantic version changes.

Existing line:

```text
pydantic[email]==2.5.0
pydantic-settings==2.1.0
email-validator>=2.0.0
```

### Railway Start Command

- **Leave empty** in Railway UI when using this Dockerfile.
- Railway will use the Dockerfile `CMD` above. Do **not** override with a custom start command unless you replicate the same logic (migrations + uvicorn with `PORT`).

### Required Railway environment variables

| Variable        | Required | Notes |
|----------------|----------|--------|
| **DATABASE_URL** | Yes     | PostgreSQL URL. If you add Railway Postgres, use the generated `DATABASE_URL` (or set it from `POSTGRES_URL`; app supports both). |
| **SECRET_KEY**   | Yes     | Min 32 chars; JWT signing. Generate with e.g. `openssl rand -hex 32`. |
| **ENVIRONMENT**  | No      | Set to `production` for production. |
| **ALLOWED_ORIGINS** | No   | Comma-separated frontend origins for CORS. |
| **PORT**         | No      | Set by Railway; do not set manually. |

SMTP/email is not required for first successful deployment; app can start without it.

---

## 3. Deployment flow (step-by-step)

1. **GitHub push**  
   You push to the branch connected to Railway (e.g. `main`).

2. **Railway build**  
   - Railway uses **Root Directory = `backend`**.  
   - Build context = `backend/`.  
   - `docker build` runs: `Dockerfile` in `backend/`, `COPY . .` = backend contents → `/app` (so `app/`, `alembic/`, `start.sh`, etc. are in `/app`).  
   - Build logs show pip install, COPY, etc. No “cd backend: no such file” if root is `backend`.

3. **Container start (deploy)**  
   - Railway starts the container and sets **PORT** in the environment (e.g. 8000 or dynamic).  
   - Container runs: `CMD ["/bin/bash", "-c", "./start.sh"]`.  
   - Bash runs `./start.sh`; that process **inherits** `PORT`.  
   - start.sh: if PORT unset or not a number → 8000; then `alembic upgrade head`; then `exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"`.  
   - Deploy logs show “Running migrations…” and “Starting uvicorn on 0.0.0.0:PORT…”.

4. **Public URL**  
   - Railway assigns a public URL (e.g. `https://your-app.up.railway.app`).  
   - Health: `GET /health` → 200.  
   - Docs: `GET /docs` → Swagger UI.  
   - Ready: `GET /ready` → 200 when DB is reachable.

---

## 4. Railway project setup (checklist)

1. **New Project** → Deploy from GitHub repo → select repo and branch.
2. **Service settings**  
   - **Root Directory:** `backend` (so Dockerfile and all paths are correct).  
   - **Dockerfile Path:** `Dockerfile` (relative to root dir = `backend/Dockerfile`).  
   - **Start Command:** leave empty (use Dockerfile CMD).
3. **Variables**  
   - `DATABASE_URL` = your Postgres URL (or from Railway Postgres).  
   - `SECRET_KEY` = long random string.  
   - Optionally `ENVIRONMENT=production`, `ALLOWED_ORIGINS=...`.
4. **Deploy**  
   - Trigger deploy; wait for build then deploy logs.  
   - Open the generated URL → `/health` and `/docs`.

---

## 5. Common mistakes and how this setup avoids them

| Mistake | Why it breaks | How we avoid it |
|--------|----------------|-------------------|
| PORT not expanding / “$PORT is not a valid integer” | Exec form `CMD ["uvicorn", ...]` doesn’t run a shell, so `$PORT` is never expanded. Or script run with `sh` and PORT not exported. | We use `CMD ["/bin/bash", "-c", "./start.sh"]` so bash runs and passes env to start.sh. start.sh validates PORT and uses `"${PORT}"`; fallback 8000 if unset or non-numeric. |
| Wrong working directory / “cd backend: no such file” | Build context = repo root, so `COPY . .` puts `backend/` as a subdir and app expects `app/` at root. | Railway **Root Directory = backend**. Build context = backend/, so `COPY . .` puts app/, start.sh, etc. in `/app`. No `cd backend` needed. |
| Missing email-validator / EmailStr error | Pydantic `EmailStr` needs the `email-validator` package. | We add `pydantic[email]` and `email-validator>=2.0.0` in requirements.txt. |
| Hardcoded port | uvicorn --port 8000 ignores Railway’s PORT; Railway can’t route. | We never hardcode; we use `--port "${PORT}"` with PORT from env and default 8000 only when PORT is missing. |
| Migrations not run / DB schema mismatch | App starts but DB is missing tables/columns. | start.sh runs `alembic upgrade head` before uvicorn; idempotent so safe on every deploy. |
| Build vs deploy logs confusion | Build = building image; deploy = running container. PORT and start script run at deploy. | We use one CMD that runs start.sh at container start; deploy logs show migrations and uvicorn with PORT. |
| .env or secrets in image | COPY . . can include .env. | Dockerfile runs `find . -name ".env" -delete`. .dockerignore also excludes .env. |

---

## 6. Verify after deploy

```bash
# Health (no DB required)
curl -s https://YOUR_RAILWAY_URL/health

# Docs (Swagger)
open https://YOUR_RAILWAY_URL/docs

# Ready (DB required)
curl -s https://YOUR_RAILWAY_URL/ready
```

Use **Root Directory = backend**, Dockerfile CMD as above, and the env vars listed; the app should deploy successfully on the first retry.

---

## 7. Anti-patterns to REMOVE (if present)

| Anti-pattern | Remove / Fix |
|--------------|--------------|
| `uvicorn ... --port $PORT` (unquoted or literal `$PORT`) | Use a numeric variable (e.g. `PORT_NUM`) and `--port "${PORT_NUM}"` so the value is always an integer. |
| `sa.Enum(..., name='x')` without `create_type=False` in migrations | Create the type with `DO $$ BEGIN CREATE TYPE ... EXCEPTION WHEN SQLSTATE '42710' THEN NULL; END $$;` first, then use `postgresql.ENUM(..., create_type=False)`. |
| `SECRET_KEY` required in Pydantic (no default) | Use `SECRET_KEY: str = ""` in Settings; validate at startup in `validate_config()` and raise in production if missing. |
| Alembic `env.py` importing config before `load_dotenv()` | Call `load_dotenv()` in `env.py` before importing `app.core.config`. |
| Hardcoded `--port 8000` in start command | Use `${PORT_NUM}` from validated PORT; default 8000 only when PORT is unset/non-numeric. |
| `WHEN duplicate_object` in PL/pgSQL for ENUMs | Use `EXCEPTION WHEN SQLSTATE '42710' THEN NULL` for idempotent ENUM creation (42710 = duplicate_object). |

---

## 8. Railway deploy checklist

- [ ] **Root Directory** = `backend`
- [ ] **Dockerfile path** = `Dockerfile` (relative to root dir)
- [ ] **Start Command** = leave empty (use Dockerfile CMD)
- [ ] **Variables:** `DATABASE_URL` (or Railway Postgres → copy `DATABASE_URL`), `SECRET_KEY` (min 32 chars)
- [ ] **Optional:** `ENVIRONMENT=production`, `ALLOWED_ORIGINS=https://your-frontend.vercel.app`
- [ ] **Do not set** `PORT` (Railway sets it)
- [ ] Deploy → open service URL → `/health` (200), `/docs` (Swagger)
- [ ] If DB already has data: ensure `alembic_version` matches your branch; do not re-run initial migration on a populated DB
