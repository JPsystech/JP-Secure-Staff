# Backend verification steps

Use these steps to confirm migrations and API after 2FA removal and templates schema fix.

## 1. Run migrations

From the **backend** directory:

```bash
cd backend
alembic upgrade head
```

Expected: No errors. Final revision should be `step15_tpl_name`.

## 2. Check single head (optional)

```bash
alembic heads
```

Expected: One line, e.g. `step15_tpl_name (head)`.

## 3. Start the API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or use `./scripts/start.sh` (runs `alembic upgrade head` then uvicorn).

## 4. Verify no DB errors

### Templates endpoint (no missing columns)

```bash
curl -s -H "Authorization: Bearer YOUR_JWT" http://localhost:8000/api/v1/templates/
```

Expected: `200 OK` and JSON array (possibly empty). No `column templates.name does not exist` or similar.

### Login endpoint (no 2FA references)

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}'
```

Expected: `200 OK` and JSON with `access_token`, `token_type`, `role`. No "role requires 2FA" or 2FA-related errors.

## 5. Confirm users table has no 2FA columns (optional)

If you have `psql` and `DATABASE_URL`:

```bash
psql "$DATABASE_URL" -c "\d users"
```

Expected: No `twofa_enabled` or `twofa_secret_encrypted` columns.

Or raw SQL:

```sql
SELECT column_name FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'users'
ORDER BY ordinal_position;
```

## 6. Confirm templates table has required columns (optional)

```sql
SELECT column_name FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'templates'
ORDER BY ordinal_position;
```

Expected columns include: `id`, `name`, `type`, `is_active`, `active_revision_id`, `created_at`, `updated_at`.

---

**Summary:** After `alembic upgrade head`, the app should run with no 2FA columns on `users`, templates table matching the ORM (`name`, `is_active`, `active_revision_id`, etc.), and `/api/v1/templates/` and login working without DB or 2FA errors.
