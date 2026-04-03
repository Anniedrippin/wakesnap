#!/usr/bin/env bash
# Render runs this on every deploy before starting the server.
set -e

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Running migrations..."
python manage.py migrate --no-input

echo "==> Seeding room objects (skips existing)..."
python seed_data.py

echo "==> Build complete ✅"