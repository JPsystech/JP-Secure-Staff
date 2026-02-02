# JP Secure Staff – Deployment & Runbook

## Railway (backend from GitHub)

**Full guide:** See **backend/RAILWAY_DEPLOY.md** for step-by-step flow, PORT handling, Dockerfile vs start command, env vars, and common mistakes.

Deploy the **backend** only from the `backend` directory so Railway uses the Dockerfile and runs migrations + uvicorn with correct PORT.

1. **Create a new project**
   - In [Railway](https://railway.app), New Project → Deploy from GitHub repo.
   - Connect the `JP-Secure-Staff` (or your repo) and choose the branch to deploy.

2. **Configure the backend service**
   - **Root directory:** Set to `backend` so the service runs from `/backend` (Procfile, `start.sh`, `requirements.txt` are used).
   - Or use **Dockerfile:** Set "Dockerfile path" to `backend/Dockerfile` (Railway will build from repo root; ensure Dockerfile context is correct, or set root to `backend` and use `Dockerfile` in root).
   - **Start command:** If using Nixpacks/Procfile, Railway will run `web: bash ./start.sh` from `backend/`. No need to set a custom start command unless you override.

3. **Environment variables** (Settings → Variables)
   - **DATABASE_URL** – PostgreSQL connection URL. If you add Railway Postgres, copy the `DATABASE_URL` (or `POSTGRES_URL`) from the Postgres service and set it here. The app accepts either `DATABASE_URL` or `POSTGRES_URL`.
   - **SECRET_KEY** – Min 32 characters; used for JWT signing. Generate a strong random value (e.g. `openssl rand -hex 32`).
   - **ENVIRONMENT** – Set to `production` for production.
   - Optional: **ALLOWED_ORIGINS** – Comma-separated frontend origins (e.g. `https://your-app.vercel.app`).

4. **Deploy**
   - Push to the connected branch or trigger a deploy. Railway will:
     - Install deps from `backend/requirements.txt` (or build from `backend/Dockerfile`).
     - Run `alembic upgrade head` (idempotent; safe if already applied).
     - Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

5. **Verify**
   - Open the deployed URL (e.g. `https://your-app.up.railway.app`).
   - **Health:** `GET https://your-app.up.railway.app/health` → 200.
   - **Docs:** `GET https://your-app.up.railway.app/docs` → Swagger UI.
   - **Ready:** `GET https://your-app.up.railway.app/ready` → 200 when DB is reachable.

6. **If build fails with "railpack could not determine how to build"**
   - Ensure **Root Directory** is set to `backend` so Railway sees `Procfile`, `requirements.txt`, and `runtime.txt`.
   - Or use **Dockerfile** with root directory `backend` and Dockerfile at `backend/Dockerfile`.

---

## Local development

1. **Backend**
   - Copy `backend/.env.example` to `backend/.env` and set `DATABASE_URL`, `SECRET_KEY`.
   - Create DB and run migrations: `cd backend && alembic upgrade head`.
   - Optional: `python scripts/seed_data.py`.
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.

2. **Frontend**
   - Copy `frontend/.env.example` to `frontend/.env.local`; set `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` if needed.
   - Start: `cd frontend && npm run dev`.

3. **Checks**
   - Backend: http://localhost:8000/health (200), http://localhost:8000/ready (200 if DB up).
   - Login: POST http://localhost:8000/api/v1/auth/login with email/password.

---

## Docker Compose (production-style)

1. **Prepare env**
   - From repo root, ensure `backend/.env` exists (or set env for compose):
     - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (defaults: postgres, postgres, jp_secure_staff).
     - `SECRET_KEY` (min 32 chars for production).
   - Optional: `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` for build.

2. **Run**
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```
   - Builds backend and frontend from `backend/Dockerfile` and `frontend/Dockerfile`.
   - Backend runs `start.sh`: `alembic upgrade head` then `uvicorn` (port from `PORT` or 8000).
   - Postgres data: volume `pgdata`. Backend uploads: volume `backend_uploads`.

3. **URLs**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Health: http://localhost:8000/health , http://localhost:8000/ready

4. **CORS**
   - Backend reads `ALLOWED_ORIGINS` (comma-separated). Compose sets it to include http://localhost:3000 and http://frontend:3000.

---

## Migrations

- **Apply**
  ```bash
  cd backend && alembic upgrade head
  ```
- **Docker / Railway**
  - Backend container runs `alembic upgrade head` on start via `start.sh` (idempotent; safe if already applied).
- **Multiple heads**
  - Run `alembic heads`; if more than one, merge:  
    `alembic merge -m "merge heads" <rev1> <rev2>` then `alembic upgrade head`.
  - Or: `python -m app.scripts.db_check` (from `backend/`) to see heads and applied revision.

---

## Backups (PostgreSQL)

- **Script:** `docker/backup/pg_backup.sh`
  - Uses `PGHOST`, `PGPORT`, `PGUSER`, `PGDATABASE`, `PGPASSWORD` (defaults: localhost, 5432, postgres, jp_secure_staff).
  - Writes to `BACKUP_DIR` (default: `docker/backup/backups`) with name `pg_<db>_<timestamp>.sql`.
  - Retention: last 7 daily; last 4 weekly (run with `BACKUP_SUFFIX=weekly` on Sunday).

- **Linux cron (daily 2am)**
  ```cron
  0 2 * * * PGPASSWORD=yourpass /path/to/docker/backup/pg_backup.sh
  ```
  Weekly (Sunday 3am):
  ```cron
  0 3 * * 0 BACKUP_SUFFIX=weekly PGPASSWORD=yourpass /path/to/docker/backup/pg_backup.sh
  ```

- **Windows Task Scheduler**
  - Create a task that runs at 2:00 AM daily.
  - Program: `bash` or `wsl`; arguments: path to `pg_backup.sh`.
  - Set env `PGPASSWORD` in the task (or use a .pgpass file).

---

## Log rotation

- Backend uses Python `RotatingFileHandler`: `logs/app.log`, 20 MB per file, 10 backups.
- Logs directory: `backend/logs` (auto-created). Console logging is unchanged.

---

## Rate limiting

- **Login:** `/api/v1/auth/login` is limited to 10 attempts per IP per 5 minutes. Excess returns **429** with message: "Too many login attempts. Please try again in a few minutes."
- Existing account lockout (e.g. failed_login_count / locked_until) is unchanged.

---

## Health endpoints

- **GET /health** – Liveness; always 200.
- **GET /ready** – Readiness; 200 if DB is reachable, 503 if not.
- **GET /api/v1/health** – Same as above (v1).
- **GET /api/v1/ready** – Detailed readiness (db, storage, email); 200 ok/degraded, 503 if DB fail.

---

## Troubleshooting

| Issue | Action |
|-------|--------|
| Backend won’t start in Docker | Check `backend/.env` or compose env: `DATABASE_URL`, `SECRET_KEY`. Check logs: `docker compose -f docker/docker-compose.yml logs backend`. |
| Login returns 429 | Rate limit: wait ~5 minutes or use another IP. |
| 503 on /ready | DB not reachable: check Postgres is running, `DATABASE_URL` host/port/user/password. |
| Multiple Alembic heads | Run `alembic merge -m "merge heads" <rev1> <rev2>`, then `alembic upgrade head`. |
| Missing columns / login error | Run `alembic upgrade head` and confirm step13 (or latest) is applied; run `python -m app.scripts.db_check`. |
| CORS errors from frontend | Set `ALLOWED_ORIGINS` on backend to include the frontend origin (e.g. http://localhost:3000). |
| Frontend can’t reach API | Set `NEXT_PUBLIC_API_URL` to backend URL (e.g. http://localhost:8000/api/v1). |

---

## Checklist before production

- [ ] Strong `SECRET_KEY` (min 32 chars).
- [ ] `DATABASE_URL` points to production DB.
- [ ] `ENVIRONMENT=production` set.
- [ ] `ALLOWED_ORIGINS` set to production frontend origin(s).
- [ ] Backups scheduled (cron or Task Scheduler).
- [ ] Migrations applied: `alembic upgrade head`.
- [ ] `/ready` returns 200 before routing traffic.
