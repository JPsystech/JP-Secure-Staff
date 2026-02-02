# Production user bootstrap

Creates initial production login users **only from ENV**, when enabled. Idempotent: users are created only if they do not already exist.

## When it runs

- **ENVIRONMENT** must be `production`
- **ENABLE_PROD_BOOTSTRAP** must be `true`

Runs once at FastAPI startup. Safe on redeploy and restart (no duplicates).

## ENV variables (production)

Set these in Render (or your host) **Environment** tab. Do **not** hardcode in code.

| Variable | Required | Example | Purpose |
|----------|----------|--------|--------|
| `ENVIRONMENT` | Yes | `production` | Must be `production` for bootstrap to run |
| `ENABLE_PROD_BOOTSTRAP` | Yes | `true` | Set to `true` to create users; set to `false` after first deploy |
| `PROD_ADMIN_EMAIL` | Yes | `admin@jpsecure.com` | Admin (SUPER_ADMIN / MASTER_ADMIN) |
| `PROD_ADMIN_PASSWORD` | Yes | *(secure)* | Hashed at runtime; never logged |
| `PROD_SUBADMIN_EMAIL` | Yes | `subadmin@jpsecure.com` | Sub-Admin (ADMIN / SUB_ADMIN) |
| `PROD_SUBADMIN_PASSWORD` | Yes | *(secure)* | Hashed at runtime |
| `PROD_OPS_EMAIL` | Yes | `ops@jpsecure.com` | Operations (MANAGER / OPS_USER) |
| `PROD_OPS_PASSWORD` | Yes | *(secure)* | Hashed at runtime |
| `PROD_FINANCE_EMAIL` | Yes | `finance@jpsecure.com` | Finance (MANAGER / FINANCE_USER) |
| `PROD_FINANCE_PASSWORD` | Yes | *(secure)* | Hashed at runtime |
| `PROD_HR_EMAIL` | Yes | `hr@jpsecure.com` | HR (MANAGER / HR_USER) |
| `PROD_HR_PASSWORD` | Yes | *(secure)* | Hashed at runtime |

## Role & department mapping

| Email | Role (DB code) | Department (DB code) |
|-------|----------------|----------------------|
| admin@jpsecure.com | MASTER_ADMIN | ADMIN |
| subadmin@jpsecure.com | SUB_ADMIN | ADMIN |
| ops@jpsecure.com | OPS_USER | OPS (Operations) |
| finance@jpsecure.com | FINANCE_USER | FIN (Finance) |
| hr@jpsecure.com | HR_USER | HR (Human Resources) |

**Prerequisite:** Departments and roles must already exist (e.g. run `scripts/seed_data.py` once, or ensure your migrations/seed create them).

## After first successful deploy

1. Verify you can log in with each account (see credentials below).
2. In Render → Service → Environment, set:
   ```bash
   ENABLE_PROD_BOOTSTRAP=false
   ```
3. Redeploy so no further auto-user creation runs.

## Logs

- **BOOTSTRAP CREATED: &lt;email&gt;** — user was created (email only; password never logged).
- **Already existed: &lt;emails&gt;** — users already present; skipped.
- **Skipped: ENVIRONMENT is not production** / **ENABLE_PROD_BOOTSTRAP is not true** — bootstrap did not run.

## Example credentials (for first-time verification)

Use the **passwords you set in ENV** (e.g. the ones from your task). Example logins:

| Email | Password (from your ENV) |
|-------|--------------------------|
| admin@jpsecure.com | `JpS@2026!Admin#01` (PROD_ADMIN_PASSWORD) |
| subadmin@jpsecure.com | `JpS@2026!Sub#01` (PROD_SUBADMIN_PASSWORD) |
| ops@jpsecure.com | `JpS@2026!Ops#01` (PROD_OPS_PASSWORD) |
| finance@jpsecure.com | `JpS@2026!Fin#01` (PROD_FINANCE_PASSWORD) |
| hr@jpsecure.com | `JpS@2026!Hr#01` (PROD_HR_PASSWORD) |

You should be able to log into production with these after the first deploy (with bootstrap enabled) and the same ENV values set.
