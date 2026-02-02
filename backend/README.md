# JP Secure Staff - Backend API

## Overview
FastAPI-based REST API for JP Secure Staff ERP system. Provides authentication, document management, ticket system, and access control.

## Prerequisites
- Python 3.9+
- PostgreSQL database
- MinIO (for file storage)
- Environment variables configured (see `.env.example`)

## Installation

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Install Playwright browser (required for PDF generation):**
```bash
python -m playwright install chromium
```
**Note:** This must be run after installing the `playwright` package. The PDF generator uses Playwright's sync API in a worker thread to avoid Windows event loop issues.

2. **Set up environment variables:**
Create a `.env` file in the `backend` directory:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/jp_secure_staff
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=jp-secure-staff
```

3. **Run database migrations:**
```bash
cd backend
alembic heads          # Should show ONE head
alembic upgrade head
```
If you see **multiple heads**, merge then upgrade:
```bash
alembic merge -m "merge heads" <head1> <head2>   # e.g. alembic merge -m "merge" step12_email_logs other_head
alembic upgrade head
```
Optional: check DB migration state: `python -m app.scripts.db_check` (from `backend/`).

4. **Seed initial data:**
```bash
python scripts/seed_data.py
```

5. **Production (Render) – bootstrap initial users:**  
   For production, set `BOOTSTRAP_ENABLED=true` and the user ENV vars (`ADMIN_EMAIL`, `ADMIN_PASSWORD`, `SUBADMIN_EMAIL`, etc.) in the Render dashboard. On first deploy, the app will create departments/roles and initial users from ENV (no hardcoded passwords). After first successful deploy, set `BOOTSTRAP_ENABLED=false` and redeploy. See [PRODUCTION_BOOTSTRAP.md](PRODUCTION_BOOTSTRAP.md). Optional CLI: `python -m app.scripts.bootstrap_users` (uses `DATABASE_URL` and same ENV vars).

## Running the API

### Development Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **Base URL:** `http://localhost:8000`
- **API Docs:** `http://localhost:8000/docs`
- **Health:** `http://localhost:8000/health` (root)
- **Health (v1):** `GET /api/v1/health` - Liveness (no DB), always 200
- **Readiness:** `GET /api/v1/ready` - DB, storage, email config; 200 ok/degraded, 503 fail
- `GET /api/v1/debug/ping` - Debug endpoint to verify auth/cookies

## Runbook

### Local run
1. Set `DATABASE_URL` in `.env`.
2. `alembic upgrade head`
3. (Optional) `python scripts/seed_data.py`
4. Start backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
5. Start frontend (from project root): `cd frontend && npm run dev`

### Production run checklist
1. Apply migrations: `alembic upgrade head`
2. Check readiness: `curl http://localhost:8000/api/v1/ready` — expect 200 with `"status": "ok"` or `"degraded"`; 503 if DB down
3. Start service: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`
4. Optional: `SCHEDULER_ENABLED=false` if running scheduler in a separate process; otherwise one worker will hold the advisory lock and run the birthday job.

### Troubleshooting
- **Multiple Alembic heads:** Run `alembic heads`. If more than one, run `alembic merge -m "merge heads" <rev1> <rev2>` then `alembic upgrade head`. Or use `python -m app.scripts.db_check` to see heads and applied revision.
- **Missing columns:** Run `alembic upgrade head`. Verify with `python -m app.scripts.db_check`.
- **Login fails / undefined column:** Ensure migrations are up to date and the User model matches the DB.

## API Endpoints

### Health & Status
- `GET /health` - Health check (root, always 200)
- `GET /api/v1/health` - Liveness, no DB (200)
- `GET /api/v1/ready` - Readiness: db, storage, email (200 ok/degraded, 503 fail)
- `GET /api/v1/debug/ping` - Debug endpoint to verify auth/cookies

### Authentication
- `POST /api/v1/auth/login` - Login with email/password
- `GET /api/v1/auth/me` - Get current user info (requires auth)

### Expected Responses

#### Health Check
```json
{
  "status": "healthy",
  "service": "JP Secure Staff API",
  "version": "1.0.0"
}
```

#### Auth Me (Authenticated)
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "MASTER_ADMIN",
  "role_name": "Master Admin",
  "dept_id": 1,
  "department": {
    "id": 1,
    "name": "Operations",
    "code": "OPS"
  },
  "is_active": true
}
```

#### Auth Me (Not Authenticated)
```json
{
  "detail": "Authentication required"
}
```
**Status Code:** 401 Unauthorized

## Error Handling

The API includes comprehensive error handling:

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User account inactive or insufficient permissions
- **404 Not Found:** Resource not found
- **422 Unprocessable Entity:** Validation error
- **500 Internal Server Error:** Unexpected server error
- **503 Service Unavailable:** Database or external service unavailable

All errors are logged with full traceback for debugging.

## CORS Configuration

The API is configured to accept requests from:
- `http://localhost:3000`
- `http://localhost:3001`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`

Credentials (cookies) are enabled for authentication.

## Database Connection

The API uses connection pooling with:
- **Pool Size:** 10 connections
- **Max Overflow:** 20 connections
- **Pool Recycle:** 3600 seconds (1 hour)
- **Pool Pre-ping:** Enabled (verifies connections before use)

If the database is temporarily unavailable, the API will return 503 Service Unavailable instead of crashing.

## Logging

Structured logging is enabled with:
- **Format:** `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Level:** INFO (can be changed via environment variable)
- **Output:** Console (stdout)

All exceptions are logged with full traceback.

## Troubleshooting

### Connection Refused / Connection Reset
1. Verify the API is running: `curl http://localhost:8000/health`
2. Check database connection: Verify PostgreSQL is running and accessible
3. Check logs for error messages
4. Verify CORS configuration if calling from frontend

### 401 Unauthorized on /auth/me
1. Verify token is included in request (Authorization header or cookie)
2. Check token expiration (default: 30 minutes)
3. Verify SECRET_KEY matches between token creation and validation
4. Check user account is active

### 503 Service Unavailable
1. Check database connection
2. Verify PostgreSQL is running
3. Check database credentials in `.env`
4. Review connection pool settings

### Server Crashes / Restarts
1. Check logs for unhandled exceptions
2. Verify all dependencies are installed
3. Check database migrations are up to date
4. Review environment variables

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
```

### Type Checking
```bash
mypy .
```

## Production Deployment

1. Set `ENVIRONMENT=production` in environment variables.
2. Run migrations: `alembic upgrade head`; verify with `GET /api/v1/ready`.
3. Use Uvicorn with workers: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`.
4. Scheduler runs only once across workers (Postgres advisory lock). Set `SCHEDULER_ENABLED=false` if you run the birthday job in a separate process.
5. Email: set `EMAIL_DRY_RUN=false` and SMTP_* in production to send real emails; otherwise emails are logged only.
6. Configure reverse proxy (Nginx) for SSL termination.
7. Set up monitoring: poll `GET /api/v1/health` (liveness) and `GET /api/v1/ready` (readiness).

## Security Notes

- Never commit `.env` file to version control
- Use strong `SECRET_KEY` in production
- Enable HTTPS in production
- Regularly rotate JWT secret keys
- Implement rate limiting for authentication endpoints
- Monitor for suspicious activity

## Support

For issues or questions, check the logs first:
```bash
# View recent logs
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log
```
