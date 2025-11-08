# Diagnose API 404 Error
# This script checks ALB, target group health, and ECS service status

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "API 404 Diagnostic Script" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Load deployment variables
if (-not (Test-Path "aws-deployment-vars.json")) {
    Write-Host "ERROR: aws-deployment-vars.json not found!" -ForegroundColor Red
    exit 1
}

$vars = Get-Content "aws-deployment-vars.json" | ConvertFrom-Json
$REGION = $vars.REGION
$ALB_ARN = $vars.ALB_ARN
$TG_ARN = $vars.TG_ARN
$ALB_DNS = $vars.ALB_DNS
$PROJECT_NAME = $vars.PROJECT_NAME

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Region: $REGION" -ForegroundColor Cyan
Write-Host "  ALB DNS: $ALB_DNS" -ForegroundColor Cyan
Write-Host "  Project: $PROJECT_NAME" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check ALB Listeners
Write-Host "Step 1: Checking ALB Listeners..." -ForegroundColor Yellow
$Listeners = aws elbv2 describe-listeners --load-balancer-arn $ALB_ARN --region $REGION --output json | ConvertFrom-Json

Write-Host "  Found $($Listeners.Listeners.Count) listener(s):" -ForegroundColor Cyan
foreach ($Listener in $Listeners.Listeners) {
    Write-Host "    Port $($Listener.Port): $($Listener.Protocol)" -ForegroundColor White
    Write-Host "      Default Action: $($Listener.DefaultActions[0].Type)" -ForegroundColor Gray
    if ($Listener.DefaultActions[0].Type -eq "forward") {
        Write-Host "      Target Group: $($Listener.DefaultActions[0].TargetGroupArn)" -ForegroundColor Gray
    }
}
Write-Host ""

# Step 2: Check Target Group Health
Write-Host "Step 2: Checking Target Group Health..." -ForegroundColor Yellow
$TargetHealth = aws elbv2 describe-target-health --target-group-arn $TG_ARN --region $REGION --output json | ConvertFrom-Json

if ($TargetHealth.TargetHealthDescriptions.Count -eq 0) {
    Write-Host "  [ERROR] No targets registered in target group!" -ForegroundColor Red
    Write-Host "  This means the ECS service is not running or tasks are not registering." -ForegroundColor Yellow
} else {
    Write-Host "  Found $($TargetHealth.TargetHealthDescriptions.Count) target(s):" -ForegroundColor Cyan
    foreach ($Target in $TargetHealth.TargetHealthDescriptions) {
        $Status = $Target.TargetHealth.State
        $Color = if ($Status -eq "healthy") { "Green" } else { "Red" }
        Write-Host "    Target: $($Target.Target.Id):$($Target.Target.Port)" -ForegroundColor White
        Write-Host "      Status: $Status" -ForegroundColor $Color
        Write-Host "      Reason: $($Target.TargetHealth.Reason)" -ForegroundColor Gray
        Write-Host "      Description: $($Target.TargetHealth.Description)" -ForegroundColor Gray
    }
}
Write-Host ""

# Step 3: Check ECS Service Status
Write-Host "Step 3: Checking ECS Service Status..." -ForegroundColor Yellow
$CLUSTER_NAME = "$PROJECT_NAME-cluster"
$SERVICE_NAME = "$PROJECT_NAME-api"

$Service = aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION --output json | ConvertFrom-Json

if ($Service.services.Count -eq 0) {
    Write-Host "  [ERROR] ECS service not found!" -ForegroundColor Red
} else {
    $Svc = $Service.services[0]
    Write-Host "  Service: $($Svc.serviceName)" -ForegroundColor Cyan
    Write-Host "    Status: $($Svc.status)" -ForegroundColor $(if ($Svc.status -eq "ACTIVE") { "Green" } else { "Yellow" })
    Write-Host "    Desired Count: $($Svc.desiredCount)" -ForegroundColor Cyan
    Write-Host "    Running Count: $($Svc.runningCount)" -ForegroundColor Cyan
    Write-Host "    Pending Count: $($Svc.pendingCount)" -ForegroundColor Cyan
    
    if ($Svc.runningCount -eq 0) {
        Write-Host "    [WARNING] No tasks are running!" -ForegroundColor Red
    }
    
    # Check task definitions
    Write-Host "    Task Definition: $($Svc.taskDefinition)" -ForegroundColor Cyan
}
Write-Host ""

# Step 4: Test Health Endpoint
Write-Host "Step 4: Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $HealthUrl = "http://$ALB_DNS/health"
    Write-Host "  Testing: $HealthUrl" -ForegroundColor Cyan
    $Response = Invoke-WebRequest -Uri $HealthUrl -Method GET -TimeoutSec 10 -ErrorAction Stop
    Write-Host "  [OK] Health check successful!" -ForegroundColor Green
    Write-Host "    Status Code: $($Response.StatusCode)" -ForegroundColor Cyan
    Write-Host "    Response: $($Response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "  [ERROR] Health check failed!" -ForegroundColor Red
    Write-Host "    Error: $_" -ForegroundColor Red
}
Write-Host ""

# Step 5: Test API Endpoint
Write-Host "Step 5: Testing API Endpoint..." -ForegroundColor Yellow
try {
    $ApiUrl = "http://$ALB_DNS/api/v1/qa/query"
    Write-Host "  Testing: $ApiUrl" -ForegroundColor Cyan
    Write-Host "  (This will fail with 422/400, but should not be 404)" -ForegroundColor Gray
    
    $Body = @{
        student_id = "00000000-0000-0000-0000-000000000000"
        query = "test"
    } | ConvertTo-Json
    
    $Response = Invoke-WebRequest -Uri $ApiUrl -Method POST -Body $Body -ContentType "application/json" -TimeoutSec 10 -ErrorAction Stop
    Write-Host "  [OK] API endpoint is reachable!" -ForegroundColor Green
    Write-Host "    Status Code: $($Response.StatusCode)" -ForegroundColor Cyan
} catch {
    $StatusCode = $_.Exception.Response.StatusCode.value__
    if ($StatusCode -eq 404) {
        Write-Host "  [ERROR] 404 Not Found - Endpoint does not exist!" -ForegroundColor Red
        Write-Host "    This suggests the backend is not running or routing is incorrect." -ForegroundColor Yellow
    } elseif ($StatusCode -eq 422 -or $StatusCode -eq 400) {
        Write-Host "  [OK] Endpoint exists (got validation error, which is expected)" -ForegroundColor Green
        Write-Host "    Status Code: $StatusCode" -ForegroundColor Cyan
    } else {
        Write-Host "  [WARNING] Unexpected error: $StatusCode" -ForegroundColor Yellow
        Write-Host "    Error: $_" -ForegroundColor Gray
    }
}
Write-Host ""

# Step 6: Check Recent Logs
Write-Host "Step 6: Checking Recent Logs..." -ForegroundColor Yellow
$LOG_GROUP = "/ecs/$SERVICE_NAME"
try {
    Write-Host "  Fetching recent logs from: $LOG_GROUP" -ForegroundColor Cyan
    $Logs = aws logs tail $LOG_GROUP --since 5m --region $REGION --format short 2>&1
    
    if ($LASTEXITCODE -eq 0 -and $Logs) {
        Write-Host "  Recent log entries:" -ForegroundColor Cyan
        $Logs | Select-Object -Last 10 | ForEach-Object {
            Write-Host "    $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "  [WARNING] No recent logs found or log group doesn't exist" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [WARNING] Could not fetch logs: $_" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Diagnostic Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$HasHealthyTargets = ($TargetHealth.TargetHealthDescriptions | Where-Object { $_.TargetHealth.State -eq "healthy" }).Count -gt 0
$HasRunningTasks = if ($Service.services.Count -gt 0) { $Service.services[0].runningCount -gt 0 } else { $false }

if (-not $HasRunningTasks) {
    Write-Host "[ACTION REQUIRED] No ECS tasks are running!" -ForegroundColor Red
    Write-Host "  Run: aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --desired-count 1 --region $REGION" -ForegroundColor Yellow
} elseif (-not $HasHealthyTargets) {
    Write-Host "[ACTION REQUIRED] No healthy targets in target group!" -ForegroundColor Red
    Write-Host "  Check ECS task logs for startup errors." -ForegroundColor Yellow
    Write-Host "  Run: aws logs tail $LOG_GROUP --follow --region $REGION" -ForegroundColor Cyan
} else {
    Write-Host "[OK] Service appears to be running with healthy targets." -ForegroundColor Green
    Write-Host "  If you're still getting 404, check:" -ForegroundColor Yellow
    Write-Host "    1. Frontend API URL configuration" -ForegroundColor Cyan
    Write-Host "    2. Backend route registration in main.py" -ForegroundColor Cyan
    Write-Host "    3. ALB listener rules (should forward all traffic)" -ForegroundColor Cyan
}

Write-Host ""

