# Deploy Frontend for Demo - Simple HTTP Setup
# This script deploys the frontend to S3 with HTTP API (no mixed content issues)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Demo Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Load deployment variables
if (-not (Test-Path "aws-deployment-vars.json")) {
    Write-Host "ERROR: aws-deployment-vars.json not found!" -ForegroundColor Red
    exit 1
}

$vars = Get-Content "aws-deployment-vars.json" | ConvertFrom-Json

$REGION = $vars.REGION
$BUCKET_NAME = $vars.BUCKET_NAME
$ALB_DNS = $vars.ALB_DNS

if (-not $BUCKET_NAME -or -not $ALB_DNS) {
    Write-Host "ERROR: Missing required variables!" -ForegroundColor Red
    exit 1
}

# Get Cognito IDs (optional)
$COGNITO_USER_POOL_ID = if ($vars.COGNITO_USER_POOL_ID) { $vars.COGNITO_USER_POOL_ID } else { $env:COGNITO_USER_POOL_ID }
$COGNITO_CLIENT_ID = if ($vars.COGNITO_CLIENT_ID) { $vars.COGNITO_CLIENT_ID } else { $env:COGNITO_CLIENT_ID }

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Region: $REGION" -ForegroundColor Cyan
Write-Host "  S3 Bucket: $BUCKET_NAME" -ForegroundColor Cyan
Write-Host "  API URL: http://$ALB_DNS/api/v1" -ForegroundColor Cyan
Write-Host "  Frontend URL: http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com" -ForegroundColor Cyan
Write-Host ""

# Navigate to frontend directory
Push-Location examples/frontend-starter

if (-not (Test-Path "package.json")) {
    Write-Host "ERROR: Frontend directory not found!" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
npm install

# Set environment variables for build (HTTP for demo)
$env:VITE_API_BASE_URL = "http://$ALB_DNS/api/v1"
if ($COGNITO_USER_POOL_ID) { $env:VITE_COGNITO_USER_POOL_ID = $COGNITO_USER_POOL_ID }
if ($COGNITO_CLIENT_ID) { $env:VITE_COGNITO_CLIENT_ID = $COGNITO_CLIENT_ID }
$env:VITE_COGNITO_REGION = $REGION

Write-Host "Environment variables set:" -ForegroundColor Yellow
Write-Host "  VITE_API_BASE_URL: $env:VITE_API_BASE_URL" -ForegroundColor Cyan
if ($COGNITO_USER_POOL_ID) {
    Write-Host "  VITE_COGNITO_USER_POOL_ID: $COGNITO_USER_POOL_ID" -ForegroundColor Cyan
    Write-Host "  VITE_COGNITO_CLIENT_ID: $COGNITO_CLIENT_ID" -ForegroundColor Cyan
} else {
    Write-Host "  VITE_COGNITO_USER_POOL_ID: (not set - using demo mode)" -ForegroundColor Yellow
    Write-Host "  VITE_COGNITO_CLIENT_ID: (not set - using demo mode)" -ForegroundColor Yellow
}
Write-Host "  VITE_COGNITO_REGION: $REGION" -ForegroundColor Cyan
Write-Host ""

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host ""

# Upload to S3
Write-Host "Uploading to S3..." -ForegroundColor Yellow
aws s3 sync dist/ "s3://$BUCKET_NAME" --delete --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Upload failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "Upload completed successfully!" -ForegroundColor Green
Write-Host ""

Pop-Location

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Demo Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Demo URL (HTTP):" -ForegroundColor Yellow
Write-Host "  http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ No mixed content issues (both HTTP)" -ForegroundColor Green
Write-Host "✅ No certificates needed" -ForegroundColor Green
Write-Host "✅ Works immediately" -ForegroundColor Green
Write-Host ""
Write-Host "Note: For production with HTTPS, use deploy-frontend.ps1 instead" -ForegroundColor Gray

