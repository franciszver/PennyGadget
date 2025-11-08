# Quick Deployment Status Check Script
# Run this anytime to check if everything is ready

$vars = Get-Content "aws-deployment-vars.json" | ConvertFrom-Json

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AWS DEPLOYMENT STATUS CHECK" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Backend Health
Write-Host "1. Backend API..." -ForegroundColor Yellow
$healthUrl = "http://$($vars.ALB_DNS)/health"
try {
    $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 10
    Write-Host "   ✅ Healthy - Status: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Not responding: $_" -ForegroundColor Red
}

# 2. ECS Service
Write-Host "`n2. ECS Service..." -ForegroundColor Yellow
$ecsStatus = aws ecs describe-services --cluster elevareai-cluster --services elevareai-api --region us-east-1 --query 'services[0].[status,runningCount,desiredCount]' --output text
$parts = $ecsStatus -split "`t"
if ($parts[0] -eq "ACTIVE" -and $parts[1] -eq $parts[2]) {
    Write-Host "   ✅ Running ($($parts[1])/$($parts[2]))" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Status: $($parts[0]), Running: $($parts[1])/$($parts[2])" -ForegroundColor Yellow
}

# 3. Target Group
Write-Host "`n3. Load Balancer Target..." -ForegroundColor Yellow
$tgHealth = aws elbv2 describe-target-health --target-group-arn $vars.TG_ARN --region us-east-1 --query 'TargetHealthDescriptions[0].TargetHealth.State' --output text
if ($tgHealth -eq "healthy") {
    Write-Host "   ✅ Healthy" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Status: $tgHealth" -ForegroundColor Yellow
}

# 4. Database
Write-Host "`n4. Database..." -ForegroundColor Yellow
$dbStatus = aws rds describe-db-instances --db-instance-identifier $vars.DB_INSTANCE_ID --region us-east-1 --query 'DBInstances[0].DBInstanceStatus' --output text
if ($dbStatus -eq "available") {
    Write-Host "   ✅ Available" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Status: $dbStatus" -ForegroundColor Yellow
}

# 5. Frontend - S3
Write-Host "`n5. Frontend (S3)..." -ForegroundColor Yellow
try {
    $s3Response = Invoke-WebRequest -Uri $vars.S3_WEBSITE_URL -UseBasicParsing -TimeoutSec 10
    Write-Host "   ✅ Accessible" -ForegroundColor Green
    Write-Host "   URL: $($vars.S3_WEBSITE_URL)" -ForegroundColor Cyan
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}

# 6. Frontend - CloudFront
Write-Host "`n6. Frontend (CloudFront)..." -ForegroundColor Yellow
$cfStatus = aws cloudfront get-distribution --id $vars.CF_DIST_ID --region us-east-1 --query 'Distribution.Status' --output text
if ($cfStatus -eq "Deployed") {
    Write-Host "   ✅ Deployed" -ForegroundColor Green
    Write-Host "   URL: https://$($vars.CF_DOMAIN)" -ForegroundColor Cyan
    try {
        $cfResponse = Invoke-WebRequest -Uri "https://$($vars.CF_DOMAIN)" -UseBasicParsing -TimeoutSec 10
        Write-Host "   ✅ Accessible via HTTPS" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  HTTPS test failed: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⏳ Status: $cfStatus (still deploying...)" -ForegroundColor Yellow
    Write-Host "   URL: https://$($vars.CF_DOMAIN)" -ForegroundColor Cyan
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Backend API:" -ForegroundColor Yellow
Write-Host "  http://$($vars.ALB_DNS)" -ForegroundColor Cyan

Write-Host "`nFrontend:" -ForegroundColor Yellow
Write-Host "  S3 (HTTP): $($vars.S3_WEBSITE_URL)" -ForegroundColor Cyan
Write-Host "  CloudFront (HTTPS): https://$($vars.CF_DOMAIN)" -ForegroundColor Cyan

Write-Host "`nDemo Users:" -ForegroundColor Yellow
Write-Host "  Email: demo_multi_goal@demo.com (or demo_multi_goals@demo.com)" -ForegroundColor White
Write-Host "  Password: demo123" -ForegroundColor White

Write-Host "`nTo test:" -ForegroundColor Yellow
Write-Host "  Start-Process '$($vars.S3_WEBSITE_URL)'" -ForegroundColor White

