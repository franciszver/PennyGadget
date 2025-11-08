# Deploy Backend v1.1.4 to AWS ECS
# This script builds, tags, pushes, and deploys the backend with version 1.1.4

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend Deployment Script v1.1.4" -ForegroundColor Cyan
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
$VERSION = "v1.1.4"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Region: $REGION" -ForegroundColor Cyan
Write-Host "  Project: $PROJECT_NAME" -ForegroundColor Cyan
Write-Host "  ECR Repository: $ECR_REPO_URI" -ForegroundColor Cyan
Write-Host "  Version: $VERSION" -ForegroundColor Cyan
Write-Host ""

# Step 1: Login to ECR
Write-Host "Step 1: Logging in to ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO_URI

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: ECR login failed!" -ForegroundColor Red
    exit 1
}

Write-Host "ECR login successful!" -ForegroundColor Green
Write-Host ""

# Step 2: Build Docker image
Write-Host "Step 2: Building Docker image..." -ForegroundColor Yellow
docker build -t "$PROJECT_NAME-api:$VERSION" -t "$PROJECT_NAME-api:latest" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Docker image built successfully!" -ForegroundColor Green
Write-Host ""

# Step 3: Tag images for ECR
Write-Host "Step 3: Tagging images for ECR..." -ForegroundColor Yellow
docker tag "${PROJECT_NAME}-api:${VERSION}" "${ECR_REPO_URI}:${VERSION}"
docker tag "${PROJECT_NAME}-api:latest" "${ECR_REPO_URI}:latest"

Write-Host "Images tagged successfully!" -ForegroundColor Green
Write-Host ""

# Step 4: Push images to ECR
Write-Host "Step 4: Pushing images to ECR..." -ForegroundColor Yellow
Write-Host "  Pushing $VERSION..." -ForegroundColor Cyan
docker push "${ECR_REPO_URI}:${VERSION}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to push $VERSION!" -ForegroundColor Red
    exit 1
}

Write-Host "  Pushing latest..." -ForegroundColor Cyan
docker push "${ECR_REPO_URI}:latest"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to push latest!" -ForegroundColor Red
    exit 1
}

Write-Host "Images pushed successfully!" -ForegroundColor Green
Write-Host ""

# Step 5: Get current task definition
Write-Host "Step 5: Getting current task definition..." -ForegroundColor Yellow
$TASK_DEF_FAMILY = "$PROJECT_NAME-api"
$CURRENT_TASK_DEF = aws ecs describe-task-definition `
    --task-definition $TASK_DEF_FAMILY `
    --region $REGION `
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

# Use the existing task-definition.json as a base and update the image
if (Test-Path "task-definition.json") {
    $TASK_DEF_JSON = Get-Content "task-definition.json" -Raw | ConvertFrom-Json
} else {
    # If file doesn't exist, use the current task definition from AWS
    $TASK_DEF_JSON = $CURRENT_TASK_DEF
}

# Update the image
$TASK_DEF_JSON.containerDefinitions[0].image = "${ECR_REPO_URI}:${VERSION}"

# Remove fields that can't be in new task definition (revision, status, etc.)
$TASK_DEF_JSON.PSObject.Properties.Remove('revision')
$TASK_DEF_JSON.PSObject.Properties.Remove('status')
$TASK_DEF_JSON.PSObject.Properties.Remove('requiresAttributes')
$TASK_DEF_JSON.PSObject.Properties.Remove('compatibilities')
$TASK_DEF_JSON.PSObject.Properties.Remove('registeredAt')
$TASK_DEF_JSON.PSObject.Properties.Remove('registeredBy')
$TASK_DEF_JSON.PSObject.Properties.Remove('taskDefinitionArn')

# Remove cpu from container definition if it exists (should be at task level)
if ($TASK_DEF_JSON.containerDefinitions[0].PSObject.Properties.Name -contains 'cpu') {
    $TASK_DEF_JSON.containerDefinitions[0].PSObject.Properties.Remove('cpu')
}

# Remove empty arrays
if ($TASK_DEF_JSON.containerDefinitions[0].PSObject.Properties.Name -contains 'mountPoints') {
    $TASK_DEF_JSON.containerDefinitions[0].PSObject.Properties.Remove('mountPoints')
}
if ($TASK_DEF_JSON.containerDefinitions[0].PSObject.Properties.Name -contains 'volumesFrom') {
    $TASK_DEF_JSON.containerDefinitions[0].PSObject.Properties.Remove('volumesFrom')
}
if ($TASK_DEF_JSON.containerDefinitions[0].PSObject.Properties.Name -contains 'systemControls') {
    $TASK_DEF_JSON.containerDefinitions[0].PSObject.Properties.Remove('systemControls')
}

# Remove hostPort from portMappings (not needed for Fargate)
if ($TASK_DEF_JSON.containerDefinitions[0].portMappings[0].PSObject.Properties.Name -contains 'hostPort') {
    $TASK_DEF_JSON.containerDefinitions[0].portMappings[0].PSObject.Properties.Remove('hostPort')
}

# Convert to JSON and save
$TASK_DEF_JSON | ConvertTo-Json -Depth 10 -Compress | Out-File -FilePath "task-def-update.json" -Encoding UTF8 -NoNewline

Write-Host "Task definition updated!" -ForegroundColor Green
Write-Host ""

# Step 7: Register new task definition
Write-Host "Step 7: Registering new task definition..." -ForegroundColor Yellow
$NEW_TASK_DEF_RESULT = aws ecs register-task-definition `
    --cli-input-json file://task-def-update.json `
    --region $REGION `
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

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Initiated!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The service is now deploying v1.1.4. This may take a few minutes." -ForegroundColor Yellow
Write-Host ""
Write-Host "Monitor deployment status:" -ForegroundColor Yellow
Write-Host "  aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION --query 'services[0].[status,runningCount,desiredCount]' --output table" -ForegroundColor Cyan
Write-Host ""
Write-Host "View service logs:" -ForegroundColor Yellow
Write-Host "  aws logs tail /ecs/$SERVICE_NAME --follow --region $REGION" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check service health:" -ForegroundColor Yellow
Write-Host "  Invoke-WebRequest -Uri http://$($vars.ALB_DNS)/health" -ForegroundColor Cyan
Write-Host ""

