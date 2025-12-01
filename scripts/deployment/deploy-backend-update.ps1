# Deploy Backend Update (Async Practice Generation)
# This script builds, tags, pushes, and deploys the backend with latest changes

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend Deployment - Async Practice Update" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Load deployment variables
if (-not (Test-Path "aws-deployment-vars.json")) {
    Write-Host "ERROR: aws-deployment-vars.json not found!" -ForegroundColor Red
    Write-Host "Please run the initial deployment script first." -ForegroundColor Red
    exit 1
}

$vars = Get-Content "aws-deployment-vars.json" | ConvertFrom-Json

$REGION = $vars.REGION
$PROJECT_NAME = $vars.PROJECT_NAME
$ECR_REPO_URI = $vars.ECR_REPO_URI
$VERSION = "latest"  # Use latest tag for this update

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Region: $REGION" -ForegroundColor Cyan
Write-Host "  Project: $PROJECT_NAME" -ForegroundColor Cyan
Write-Host "  ECR Repository: $ECR_REPO_URI" -ForegroundColor Cyan
Write-Host "  Version: $VERSION" -ForegroundColor Cyan
Write-Host ""

# Set AWS profile
$env:AWS_PROFILE = "default1"

# Step 1: Login to ECR
Write-Host "Step 1: Logging in to ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $REGION --profile default1 | docker login --username AWS --password-stdin $ECR_REPO_URI

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: ECR login failed!" -ForegroundColor Red
    exit 1
}

Write-Host "ECR login successful!" -ForegroundColor Green
Write-Host ""

# Step 2: Build Docker image (with --no-cache to ensure latest code)
Write-Host "Step 2: Building Docker image (no cache)..." -ForegroundColor Yellow
docker build --no-cache -t "$PROJECT_NAME-api:latest" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Docker image built successfully!" -ForegroundColor Green
Write-Host ""

# Step 3: Tag image for ECR
Write-Host "Step 3: Tagging image for ECR..." -ForegroundColor Yellow
docker tag "${PROJECT_NAME}-api:latest" "${ECR_REPO_URI}:latest"

Write-Host "Image tagged successfully!" -ForegroundColor Green
Write-Host ""

# Step 4: Push image to ECR
Write-Host "Step 4: Pushing image to ECR..." -ForegroundColor Yellow
docker push "${ECR_REPO_URI}:latest"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to push image!" -ForegroundColor Red
    exit 1
}

Write-Host "Image pushed successfully!" -ForegroundColor Green
Write-Host ""

# Step 5: Get current task definition
Write-Host "Step 5: Getting current task definition..." -ForegroundColor Yellow
$TASK_DEF_FAMILY = "$PROJECT_NAME-api"
$CURRENT_TASK_DEF = aws ecs describe-task-definition `
    --task-definition $TASK_DEF_FAMILY `
    --region $REGION `
    --profile default1 `
    --query 'taskDefinition' `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to get task definition!" -ForegroundColor Red
    exit 1
}

Write-Host "Current task definition revision: $($CURRENT_TASK_DEF.revision)" -ForegroundColor Cyan
Write-Host ""

# Step 6: Update task definition with new image
Write-Host "Step 6: Updating task definition with new image..." -ForegroundColor Yellow

# Get current task definition as JSON
aws ecs describe-task-definition `
    --task-definition $TASK_DEF_FAMILY `
    --region $REGION `
    --profile default1 `
    --query 'taskDefinition' `
    --output json | Out-File -FilePath "current-task-def.json" -Encoding UTF8

# Use Python to update the image
python scripts/deployment/update-task-def-image.py current-task-def.json "${ECR_REPO_URI}:latest" task-def-update.json

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to update task definition JSON!" -ForegroundColor Red
    exit 1
}

Write-Host "Task definition prepared!" -ForegroundColor Green
Write-Host ""

# Step 7: Register new task definition
Write-Host "Step 7: Registering new task definition..." -ForegroundColor Yellow
$NEW_TASK_DEF_RESULT = aws ecs register-task-definition `
    --cli-input-json file://task-def-update.json `
    --region $REGION `
    --profile default1 `
    --query 'taskDefinition.{Family:family,Revision:revision,Status:status}' `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to register task definition!" -ForegroundColor Red
    exit 1
}

Write-Host "New task definition registered:" -ForegroundColor Green
Write-Host "  Family: $($NEW_TASK_DEF_RESULT.Family)" -ForegroundColor Cyan
Write-Host "  Revision: $($NEW_TASK_DEF_RESULT.Revision)" -ForegroundColor Cyan
Write-Host "  Status: $($NEW_TASK_DEF_RESULT.Status)" -ForegroundColor Cyan
Write-Host ""

# Step 8: Update ECS service
Write-Host "Step 8: Updating ECS service..." -ForegroundColor Yellow
$CLUSTER_NAME = "$PROJECT_NAME-cluster"
$SERVICE_NAME = "$PROJECT_NAME-api"
$NEW_TASK_DEF_ARN = "${TASK_DEF_FAMILY}:$($NEW_TASK_DEF_RESULT.Revision)"

$UPDATE_RESULT = aws ecs update-service `
    --cluster $CLUSTER_NAME `
    --service $SERVICE_NAME `
    --task-definition $NEW_TASK_DEF_ARN `
    --region $REGION `
    --profile default1 `
    --force-new-deployment `
    --query 'service.{ServiceName:serviceName,Status:status,TaskDefinition:taskDefinition,DesiredCount:desiredCount,RunningCount:runningCount}' `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to update ECS service!" -ForegroundColor Red
    exit 1
}

Write-Host "ECS service update initiated:" -ForegroundColor Green
Write-Host "  Service: $($UPDATE_RESULT.ServiceName)" -ForegroundColor Cyan
Write-Host "  Status: $($UPDATE_RESULT.Status)" -ForegroundColor Cyan
Write-Host "  Task Definition: $($UPDATE_RESULT.TaskDefinition)" -ForegroundColor Cyan
Write-Host "  Desired Count: $($UPDATE_RESULT.DesiredCount)" -ForegroundColor Cyan
Write-Host "  Running Count: $($UPDATE_RESULT.RunningCount)" -ForegroundColor Cyan
Write-Host ""

# Cleanup
Remove-Item "task-def-update.json" -ErrorAction SilentlyContinue
Remove-Item "current-task-def.json" -ErrorAction SilentlyContinue

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Backend deployment initiated!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The new deployment will be available in 2-3 minutes." -ForegroundColor Yellow
Write-Host "Monitor deployment status:" -ForegroundColor Cyan
Write-Host "  aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION --profile default1 --query 'services[0].[status,runningCount,desiredCount]' --output table" -ForegroundColor Gray
Write-Host ""
Write-Host "Check logs:" -ForegroundColor Cyan
Write-Host "  aws logs tail /ecs/$PROJECT_NAME-api --follow --region $REGION --profile default1" -ForegroundColor Gray
Write-Host ""

