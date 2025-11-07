# Start AI Study Companion API Server
# Usage: .\START_SERVER.ps1

Write-Host "Starting AI Study Companion API Server..." -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version
    Write-Host "Python: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "Error: Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check if uvicorn is available
try {
    python -m uvicorn --version | Out-Null
    Write-Host "Uvicorn: Available" -ForegroundColor Cyan
} catch {
    Write-Host "Installing uvicorn..." -ForegroundColor Yellow
    python -m pip install uvicorn[standard] fastapi
}

Write-Host ""
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

