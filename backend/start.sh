#!/bin/sh
set -e

if [ "${BOOTSTRAP_DB_ON_START:-0}" = "1" ]; then
  echo "BOOTSTRAP_DB_ON_START=1, running explicit bootstrap..."
  if [ "${SEED_DATA_ON_START:-0}" = "1" ]; then
    python scripts/bootstrap_db.py --seed
  else
    python scripts/bootstrap_db.py
  fi
else
  echo "Skipping database bootstrap on normal startup."
  echo "If this is a fresh or legacy database, run: python scripts/bootstrap_db.py [--seed]"
fi

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
