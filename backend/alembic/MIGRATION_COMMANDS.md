# Alembic: templates table fix (production-blocking DB mismatch)

If you see `column templates.name does not exist`, run migrations as below.

## 1. Check current heads (optional; only if you see "multiple head revisions")

```bash
cd backend
alembic heads
```

If you see **more than one** head, merge them (replace `<head1>` and `<head2>` with the revision IDs from the output):

```bash
alembic merge -m "merge heads" <head1> <head2>
```

Then run upgrade (step 3).

## 2. Apply all pending migrations

```bash
cd backend
alembic upgrade head
```

## 3. Verify templates table (optional)

**psql:**

```bash
psql $DATABASE_URL -c "\d templates"
```

**Or raw SQL:**

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'templates'
ORDER BY ordinal_position;
```

Expected columns include: `id`, `name`, `type`, `is_active`, `active_revision_id`, `created_at`, `updated_at`.

## Summary

- **Single head:** `alembic heads` → then `alembic upgrade head`.
- **Multiple heads:** `alembic merge -m "merge heads" <head1> <head2>` → then `alembic upgrade head`.
- After upgrade, `/api/v1/templates` and template creation should work without 503 or missing-column errors.
