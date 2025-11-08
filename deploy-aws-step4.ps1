# AWS Deployment - Step 4: Test Backend, Run Migrations, Create Demo Users
# Load variables
$vars = Get-Content "aws-deployment-vars.json" | ConvertFrom-Json

$REGION = $vars.REGION
$PROJECT_NAME = $vars.PROJECT_NAME
$DB_ENDPOINT = $vars.DB_ENDPOINT
$DB_PASSWORD = $vars.DB_PASSWORD
$ALB_DNS = $vars.ALB_DNS

# Step 17: Test Backend API
Write-Host "Step 17: Testing backend API..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

$HEALTH_URL = "http://$ALB_DNS/health"
Write-Host "Health check URL: $HEALTH_URL" -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri $HEALTH_URL -UseBasicParsing -TimeoutSec 10
    Write-Host "Backend is healthy! Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)" -ForegroundColor Green
} catch {
    Write-Host "Backend not ready yet. Error: $_" -ForegroundColor Yellow
    Write-Host "Wait a bit longer and check: $HEALTH_URL" -ForegroundColor Cyan
}

# Step 18: Run Database Migrations
Write-Host "`nStep 18: Running database migrations..." -ForegroundColor Cyan

# Set environment variables for migration script
$env:DB_HOST = $DB_ENDPOINT
$env:DB_PORT = "5432"
$env:DB_NAME = "elevareai"
$env:DB_USER = "elevareai_admin"
$env:DB_PASSWORD = $DB_PASSWORD

Write-Host "Running migrations..." -ForegroundColor Yellow
python scripts/run_migrations_aws.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Migration failed. Please check the error above." -ForegroundColor Red
    Write-Host "You can also run migrations manually:" -ForegroundColor Yellow
    Write-Host "  python scripts/run_migrations_aws.py --host $DB_ENDPOINT --database elevareai --user elevareai_admin --password $DB_PASSWORD" -ForegroundColor Cyan
    exit 1
}

Write-Host "Migrations completed successfully!" -ForegroundColor Green

# Step 19: Create Demo Users
Write-Host "`nStep 19: Creating demo users..." -ForegroundColor Cyan

# Set environment variables for demo user script
$env:DB_HOST = $DB_ENDPOINT
$env:DB_PORT = "5432"
$env:DB_NAME = "elevareai"
$env:DB_USER = "elevareai_admin"
$env:DB_PASSWORD = $DB_PASSWORD

Write-Host "Running demo user creation script..." -ForegroundColor Yellow
python scripts/create_demo_users.py

Write-Host "Verifying demo users..." -ForegroundColor Yellow
python scripts/verify_all_demo_accounts.py

Write-Host "`nNext: Run deploy-aws-step5.ps1 to deploy frontend" -ForegroundColor Cyan

