# Production user bootstrap

Creates initial **departments** (OPERATIONS, FINANCE, HR, ADMIN), **roles**, and **login users** from ENV when `BOOTSTRAP_ENABLED=true`. Idempotent: nothing is recreated if it already exists. Fixes production login 401 by creating missing users.

## When it runs

- **BOOTSTRAP_ENABLED** must be `"true"` (default is `"false"`).

Runs once at FastAPI startup. Safe on redeploy and restart (no duplicates). After first successful deploy, set `BOOTSTRAP_ENABLED=false` in Render and redeploy.

## Environment variables (Render dashboard)

Set these in **Render → Your Web Service → Environment**. Do **not** hardcode in code.

| Variable | Required | Default | Purpose |
|----------|----------|---------|--------|
| `BOOTSTRAP_ENABLED` | Yes | `false` | Set to `true` for first deploy only; then set back to `false` |
| `ADMIN_EMAIL` | Yes | — | Admin (Master Admin) |
| `ADMIN_PASSWORD` | Yes | — | Hashed at runtime; never logged |
| `SUBADMIN_EMAIL` | Yes | — | Sub-Admin |
| `SUBADMIN_PASSWORD` | Yes | — | Hashed at runtime |
| `OPS_EMAIL` | Yes | — | Operations user |
| `OPS_PASSWORD` | Yes | — | Hashed at runtime |
| `FINANCE_EMAIL` | Yes | — | Finance user |
| `FINANCE_PASSWORD` | Yes | — | Hashed at runtime |
| `HR_EMAIL` | Yes | — | HR user |
| `HR_PASSWORD` | Yes | — | Hashed at runtime |
| `DEFAULT_PASSWORD_CHANGE_REQUIRED` | No | `false` | Set to `true` to force password change on first login |

## Role & department mapping

| User | Role (DB) | Department (DB) |
|------|-----------|-----------------|
| ADMIN_EMAIL | MASTER_ADMIN | ADMIN (Administration) |
| SUBADMIN_EMAIL | SUB_ADMIN | ADMIN |
| OPS_EMAIL | OPS_USER | OPS (Operations) |
| FINANCE_EMAIL | FINANCE_USER | FIN (Finance) |
| HR_EMAIL | HR_USER | HR (Human Resources) |

Bootstrap ensures **departments** (ADMIN, OPS, FIN, HR) and **roles** (MASTER_ADMIN, SUB_ADMIN, OPS_USER, FINANCE_USER, HR_USER) exist; it creates them if missing. Then it creates users only if the email does not already exist (case-insensitive).

## Logs (no plaintext passwords)

- **Bootstrap user created: &lt;email&gt;** — user was created.
- **Bootstrap user exists: &lt;email&gt;** — user already present; skipped.
- **Skipped: BOOTSTRAP_ENABLED is not true** — bootstrap did not run.

## Render: enable for one deploy, then disable

1. **First deploy:** In Render → Service → **Environment**, add:
   - `BOOTSTRAP_ENABLED` = `true`
   - `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `SUBADMIN_EMAIL`, `SUBADMIN_PASSWORD`, `OPS_EMAIL`, `OPS_PASSWORD`, `FINANCE_EMAIL`, `FINANCE_PASSWORD`, `HR_EMAIL`, `HR_PASSWORD` (use strong passwords).
2. Deploy. Check logs for "Bootstrap user created: &lt;email&gt;" to confirm users were created.
3. **After first successful deploy:** Set `BOOTSTRAP_ENABLED` = `false` and redeploy so no further auto-user creation runs.
4. Log in at `/api/v1/auth/login` with the same credentials you set in ENV.

## CLI (manual run)

From **backend** directory, with `DATABASE_URL` (or `POSTGRES_URL`) and the same ENV vars set:

```bash
python -m app.scripts.bootstrap_users
```

Uses the same logic as startup; useful for one-off seeding or debugging.

## `/api/v1/auth/login` in production

Once bootstrap has run with `BOOTSTRAP_ENABLED=true` and the env-provided credentials are set, production login works: users exist in the DB with hashed passwords, so `/api/v1/auth/login` returns 200 and a token instead of 401.
