# Quick Setup Script (PowerShell)
# Sets up the entire development environment quickly

$ErrorActionPreference = "Stop"

Write-Host "[SETUP] AI Study Companion - Quick Setup" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Node.js
$skipFrontend = $false
try {
    $nodeVersion = node --version 2>&1
    Write-Host "[OK] Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Node.js not found. Frontend setup will be skipped." -ForegroundColor Yellow
    $skipFrontend = $true
}

# Create virtual environment
Write-Host "[SETUP] Setting up Python environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

# Install Python dependencies
Write-Host "[SETUP] Installing Python dependencies..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "[OK] Python dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Some dependencies may have failed to install." -ForegroundColor Yellow
    Write-Host "[INFO] If psycopg2-binary failed, you may need PostgreSQL development libraries." -ForegroundColor Yellow
    Write-Host "[INFO] For Windows, you can try: pip install psycopg2-binary --no-build-isolation" -ForegroundColor Yellow
}

# Set up database
Write-Host "[SETUP] Setting up database..." -ForegroundColor Yellow
if (Test-Path ".env") {
    python scripts/setup_db.py
    Write-Host "[OK] Database setup complete" -ForegroundColor Green
} else {
    Write-Host "[WARN] .env file not found. Creating from example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-Host "[OK] .env file created. Please update with your configuration." -ForegroundColor Green
    }
}

# Set up frontend (if Node.js is available)
if (-not $skipFrontend -and (Test-Path "examples/frontend-starter")) {
    Write-Host "[SETUP] Setting up frontend..." -ForegroundColor Yellow
    Push-Location examples/frontend-starter
    if (-not (Test-Path "node_modules")) {
        npm install
        Write-Host "[OK] Frontend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "[OK] Frontend dependencies already installed" -ForegroundColor Green
    }
    Pop-Location
}

Write-Host ""
Write-Host "[OK] Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Update .env with your configuration"
Write-Host "2. Start the API: python -m uvicorn src.api.main:app --reload"
Write-Host "3. Start the frontend: cd examples/frontend-starter && npm run dev"
Write-Host ""
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "API docs at: http://localhost:8000/docs" -ForegroundColor Cyan

