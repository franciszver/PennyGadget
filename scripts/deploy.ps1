# Deployment Script for AI Study Companion API (PowerShell)
# Usage: .\scripts\deploy.ps1 [environment]

param(
    [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "AI Study Companion - Deployment Script" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker is not installed" -ForegroundColor Red
    exit 1
}

# Check if docker-compose is installed
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "Error: docker-compose is not installed" -ForegroundColor Red
    exit 1
}

# Load environment variables
$envFile = Join-Path $ProjectDir ".env.$Environment"
if (Test-Path $envFile) {
    Write-Host "Loading environment variables from .env.$Environment" -ForegroundColor Green
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
} elseif (Test-Path (Join-Path $ProjectDir ".env")) {
    Write-Host "Warning: Using .env file (consider using .env.$Environment)" -ForegroundColor Yellow
    Get-Content (Join-Path $ProjectDir ".env") | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
} else {
    Write-Host "Warning: No .env file found. Using defaults." -ForegroundColor Yellow
}

Set-Location $ProjectDir

# Build Docker image
Write-Host ""
Write-Host "Building Docker image..." -ForegroundColor Green
docker-compose build --no-cache api

# Run database migrations (if using Alembic)
if (Test-Path (Join-Path $ProjectDir "alembic.ini")) {
    Write-Host ""
    Write-Host "Running database migrations..." -ForegroundColor Green
    docker-compose run --rm api alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Migrations failed or not configured" -ForegroundColor Yellow
    }
}

# Start services
Write-Host ""
Write-Host "Starting services..." -ForegroundColor Green
docker-compose up -d

# Wait for services to be healthy
Write-Host ""
Write-Host "Waiting for services to be healthy..." -ForegroundColor Green
$timeout = 60
$elapsed = 0
while ($elapsed -lt $timeout) {
    $status = docker-compose ps
    if ($status -match "healthy") {
        Write-Host "Services are healthy!" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
    $elapsed += 2
    Write-Host "." -NoNewline
}

if ($elapsed -ge $timeout) {
    Write-Host "Timeout waiting for services to be healthy" -ForegroundColor Red
    docker-compose logs
    exit 1
}

# Health check
Write-Host ""
Write-Host "Performing health check..." -ForegroundColor Green
Start-Sleep -Seconds 5
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Health check passed!" -ForegroundColor Green
    } else {
        throw "Health check failed"
    }
} catch {
    Write-Host "❌ Health check failed" -ForegroundColor Red
    docker-compose logs api
    exit 1
}

# Display service status
Write-Host ""
Write-Host "Service Status:" -ForegroundColor Green
docker-compose ps

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API URL: http://localhost:8000"
Write-Host "API Docs: http://localhost:8000/docs"
Write-Host "Health: http://localhost:8000/health"
Write-Host ""
Write-Host "To view logs: docker-compose logs -f api"
Write-Host "To stop: docker-compose down"
Write-Host ""

