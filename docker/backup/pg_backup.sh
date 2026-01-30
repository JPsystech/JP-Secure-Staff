#!/bin/sh
# PostgreSQL backup for JP Secure Staff.
# Retention: keep last 7 daily; keep last 4 weekly (files named *_weekly_*).
# Schedule: cron "0 2 * * *" (daily 2am). For weekly: 0 3 * * 0 with BACKUP_SUFFIX=weekly
# Windows: use Task Scheduler to run this script or pg_dump.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$SCRIPT_DIR/backups}"
mkdir -p "$BACKUP_DIR"

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-postgres}"
PGDATABASE="${PGDATABASE:-jp_secure_staff}"
PGPASSWORD="${PGPASSWORD:-}"

export PGPASSWORD
STAMP=$(date +%Y%m%d_%H%M%S)
SUFFIX="${BACKUP_SUFFIX:-}"
FILE="$BACKUP_DIR/pg_${PGDATABASE}_${STAMP}${SUFFIX:+_$SUFFIX}.sql"

echo "Backing up $PGDATABASE to $FILE"
pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -F p -f "$FILE"
unset PGPASSWORD
echo "Created $FILE"

# Retention: keep last 7 daily (non-weekly) and last 4 weekly
cd "$BACKUP_DIR"
# Delete daily backups beyond the 7 most recent (by mtime)
ls -t pg_${PGDATABASE}_*.sql 2>/dev/null | grep -v _weekly_ | tail -n +8 | while read f; do
  rm -f "$f" && echo "Removed old daily $f"
done
# Delete weekly backups beyond the 4 most recent
ls -t pg_${PGDATABASE}_*_weekly_*.sql 2>/dev/null | tail -n +5 | while read f; do
  rm -f "$f" && echo "Removed old weekly $f"
done
echo "Backup and retention done."
