# Stop on error
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================"
Write-Host "        WakeSnap Launcher"
Write-Host "========================================"
Write-Host ""

# Get script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKEND = Join-Path $SCRIPT_DIR "backend"

# 1. Migrate
Write-Host "Running Django migrations..."
Set-Location $BACKEND
python manage.py migrate --run-syncdb -v 0

# 2. Seed objects if empty
Write-Host "Seeding room objects..."
python seed_data.py

# 3. Start FastAPI
Write-Host ""
Write-Host "Starting FastAPI on http://localhost:8000"
Write-Host "API docs at http://localhost:8000/docs"
Write-Host ""
Write-Host "----------------------------------------"
Write-Host "Open frontend/index.html in browser"
Write-Host "----------------------------------------"
Write-Host ""

uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload