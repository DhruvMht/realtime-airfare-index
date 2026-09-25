#!/bin/bash
set -e

# Check if SQLite database exists and has data
if [ ! -f /app/data/apix.db ]; then
    echo "[APIx Entrypoint] Database not found. Initializing database and seeding 90-day baseline..."
    python scripts/init_db.py
else
    echo "[APIx Entrypoint] Existing database detected at /app/data/apix.db."
fi

# Execute the container command
exec "$@"
