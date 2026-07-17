#!/bin/bash
set -e

echo "Menjalankan migrasi database otomatis (Alembic)..."
alembic upgrade head

echo "Menyalakan server backend FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
