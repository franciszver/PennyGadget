# Deploy to Staging Environment (PowerShell)
# This script automates the deployment process to staging

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Staging Deployment..." -ForegroundColor Green

# Check if .env.staging exists
if (-not (Test-Path .env.staging)) {
    Write-Host "❌ .env.staging not found. Run: python scripts/create_staging_env.py" -ForegroundColor Red
    exit 1
}

# Build Docker image
Write-Host "📦 Building Docker image..." -ForegroundColor Yellow
docker build -t pennygadget-api:staging .

# Stop existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.staging.yml down

# Start containers
Write-Host "▶️  Starting staging environment..." -ForegroundColor Yellow
docker-compose -f docker-compose.staging.yml up -d

# Wait for database to be ready
Write-Host "⏳ Waiting for database..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Run migrations
Write-Host "🔄 Running database migrations..." -ForegroundColor Yellow
docker-compose -f docker-compose.staging.yml exec -T api python scripts/setup_db.py

# Seed test data (optional)
$seedData = Read-Host "Seed test data? (y/n)"
if ($seedData -eq "y" -or $seedData -eq "Y") {
    Write-Host "🌱 Seeding test data..." -ForegroundColor Yellow
    docker-compose -f docker-compose.staging.yml exec -T api python scripts/seed_demo_data.py
}

# Health check
Write-Host "🏥 Checking API health..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    Write-Host "✅ Health check passed!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Health check failed - check logs" -ForegroundColor Yellow
}

Write-Host "✅ Staging deployment complete!" -ForegroundColor Green
Write-Host "📊 API available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API docs at: http://localhost:8000/docs" -ForegroundColor Cyan

