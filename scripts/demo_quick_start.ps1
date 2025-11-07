# Quick Demo Setup Script (PowerShell)
# Sets up environment for demo

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "AI Study Companion - Demo Quick Start" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if server is running
Write-Host "[1/4] Checking server status..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[OK] Server is running" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Server not running. Start with: python run_server.py" -ForegroundColor Yellow
}

# Check database connection
Write-Host ""
Write-Host "[2/4] Checking database connection..." -ForegroundColor Yellow
python -c "from src.config.database import engine; from sqlalchemy import text; conn = engine.connect(); result = conn.execute(text('SELECT 1')); result.fetchone(); print('[OK] Database connected')" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Database connected" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Database connection failed" -ForegroundColor Red
}

# Check demo data
Write-Host ""
Write-Host "[3/4] Checking demo data..." -ForegroundColor Yellow
if (Test-Path "scripts/demo_data.json") {
    Write-Host "[OK] Demo data file exists" -ForegroundColor Green
} else {
    Write-Host "[INFO] Run 'python scripts/seed_demo_data.py' to generate demo data" -ForegroundColor Cyan
}

# Show available endpoints
Write-Host ""
Write-Host "[4/4] Available Demo Endpoints:" -ForegroundColor Yellow
Write-Host "  - Health: GET http://localhost:8000/health"
Write-Host "  - API Docs: http://localhost:8000/docs"
Write-Host "  - Summaries: POST http://localhost:8000/api/v1/summaries"
Write-Host "  - Practice: POST http://localhost:8000/api/v1/practice/assign"
Write-Host "  - Q&A: POST http://localhost:8000/api/v1/qa/query"
Write-Host "  - Progress: GET http://localhost:8000/api/v1/progress/{student_id}"
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Demo Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "See DEMO_GUIDE.md for demo scenarios" -ForegroundColor Cyan
Write-Host ""

