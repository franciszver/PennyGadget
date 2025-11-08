# AWS Deployment - Step 3: Create Task Definition and Deploy Service
# Load variables
$vars = Get-Content "aws-deployment-vars.json" | ConvertFrom-Json

$ACCOUNT_ID = $vars.ACCOUNT_ID
$REGION = $vars.REGION
$PROJECT_NAME = $vars.PROJECT_NAME
$VPC_ID = $vars.VPC_ID
$SUBNETS = $vars.SUBNETS
$RDS_SG_ID = $vars.RDS_SG_ID
$ECS_SG_ID = $vars.ECS_SG_ID
$DB_PASSWORD = $vars.DB_PASSWORD
$DB_ENDPOINT = $vars.DB_ENDPOINT
$ECR_REPO_URI = $vars.ECR_REPO_URI
$ECS_TASK_ROLE_ARN = $vars.ECS_TASK_ROLE_ARN

# Get Cognito IDs from vars file or environment variables
$COGNITO_USER_POOL_ID = if ($vars.COGNITO_USER_POOL_ID) { $vars.COGNITO_USER_POOL_ID } else { $env:COGNITO_USER_POOL_ID }
$COGNITO_CLIENT_ID = if ($vars.COGNITO_CLIENT_ID) { $vars.COGNITO_CLIENT_ID } else { $env:COGNITO_CLIENT_ID }

if (-not $COGNITO_USER_POOL_ID -or -not $COGNITO_CLIENT_ID) {
    Write-Host "ERROR: Cognito credentials not found!" -ForegroundColor Red
    Write-Host "Please set COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID environment variables" -ForegroundColor Red
    Write-Host "Or add them to aws-deployment-vars.json" -ForegroundColor Red
    exit 1
}

# Get OpenAI API key from environment variable
$OPENAI_API_KEY = $env:OPENAI_API_KEY
if (-not $OPENAI_API_KEY) {
    Write-Host "ERROR: OPENAI_API_KEY not found in environment!" -ForegroundColor Red
    Write-Host "Please set: `$env:OPENAI_API_KEY = 'sk-...'" -ForegroundColor Red
    exit 1
}

# Validate OpenAI key format
if ($OPENAI_API_KEY -notlike "sk-*") {
    Write-Host "WARNING: OpenAI API key format may be invalid (should start with 'sk-')" -ForegroundColor Yellow
}
Write-Host "Using OpenAI API key (format validated)" -ForegroundColor Green

# Step 11: Create ECS Task Definition
Write-Host "Step 11: Creating ECS task definition..." -ForegroundColor Cyan

$TASK_DEF_JSON = @{
    family = "$PROJECT_NAME-api"
    networkMode = "awsvpc"
    requiresCompatibilities = @("FARGATE")
    cpu = "256"
    memory = "512"
    executionRoleArn = $ECS_TASK_ROLE_ARN
    taskRoleArn = $ECS_TASK_ROLE_ARN
    containerDefinitions = @(
        @{
            name = "$PROJECT_NAME-api"
            image = "$ECR_REPO_URI:latest"
            essential = $true
            portMappings = @(
                @{
                    containerPort = 8000
                    protocol = "tcp"
                }
            )
            environment = @(
                @{ name = "DB_HOST"; value = $DB_ENDPOINT }
                @{ name = "DB_PORT"; value = "5432" }
                @{ name = "DB_NAME"; value = "elevareai" }
                @{ name = "DB_USER"; value = "elevareai_admin" }
                @{ name = "DB_PASSWORD"; value = $DB_PASSWORD }
                @{ name = "COGNITO_USER_POOL_ID"; value = $COGNITO_USER_POOL_ID }
                @{ name = "COGNITO_CLIENT_ID"; value = $COGNITO_CLIENT_ID }
                @{ name = "COGNITO_REGION"; value = $REGION }
                @{ name = "OPENAI_API_KEY"; value = $OPENAI_API_KEY }
                @{ name = "ENVIRONMENT"; value = "production" }
                @{ name = "LOG_LEVEL"; value = "INFO" }
            )
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/$PROJECT_NAME-api"
                    "awslogs-region" = $REGION
                    "awslogs-stream-prefix" = "ecs"
                }
            }
            healthCheck = @{
                command = @("CMD-SHELL", "curl -f http://localhost:8000/health || exit 1")
                interval = 30
                timeout = 5
                retries = 3
                startPeriod = 60
            }
        }
    )
} | ConvertTo-Json -Depth 10

$TASK_DEF_JSON | Out-File -FilePath "task-definition.json" -Encoding UTF8

aws ecs register-task-definition --cli-input-json file://task-definition.json --region $REGION
Write-Host "Task definition registered!" -ForegroundColor Green

# Step 13: Create Application Load Balancer
Write-Host "`nStep 13: Creating Application Load Balancer..." -ForegroundColor Cyan
$ALB_NAME = "$PROJECT_NAME-alb"

# Convert subnet string to array (subnets are space-separated)
$SUBNET_ARRAY = $SUBNETS -split '\s+' | Where-Object { $_ -ne '' }
$SUBNET_LIST = $SUBNET_ARRAY | Select-Object -First 2

$ALB_ARN = aws elbv2 create-load-balancer --name $ALB_NAME --subnets $SUBNET_LIST --security-groups $ECS_SG_ID --region $REGION --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "ALB may already exist, checking..." -ForegroundColor Yellow
    $ALB_ARN = aws elbv2 describe-load-balancers --names $ALB_NAME --region $REGION --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>&1
    if ([string]::IsNullOrWhiteSpace($ALB_ARN)) {
        Write-Host "Failed to create or find ALB. Error: $ALB_ARN" -ForegroundColor Red
        exit 1
    }
}

$ALB_DNS = aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --region $REGION --query 'LoadBalancers[0].DNSName' --output text
Write-Host "ALB DNS Name: $ALB_DNS" -ForegroundColor Green

# Step 14: Create Target Group
Write-Host "`nStep 14: Creating target group..." -ForegroundColor Cyan
$TG_NAME = "$PROJECT_NAME-api-tg"
$TG_ARN = aws elbv2 create-target-group --name $TG_NAME --protocol HTTP --port 8000 --vpc-id $VPC_ID --target-type ip --health-check-path /health --health-check-interval-seconds 30 --health-check-timeout-seconds 5 --healthy-threshold-count 2 --unhealthy-threshold-count 3 --region $REGION --query 'TargetGroups[0].TargetGroupArn' --output text
Write-Host "Target Group ARN: $TG_ARN" -ForegroundColor Green

# Step 15: Create ALB Listener
Write-Host "`nStep 15: Creating ALB listener..." -ForegroundColor Cyan
$LISTENER_RESULT = aws elbv2 create-listener --load-balancer-arn $ALB_ARN --protocol HTTP --port 80 --default-actions Type=forward,TargetGroupArn=$TG_ARN --region $REGION 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "ALB listener created (HTTP)" -ForegroundColor Green
} else {
    Write-Host "Listener may already exist: $LISTENER_RESULT" -ForegroundColor Yellow
}

# Step 16: Create ECS Service
Write-Host "`nStep 16: Creating ECS service..." -ForegroundColor Cyan
# Convert subnet string to array and take first 2
$SUBNET_ARRAY = $SUBNETS -split '\s+' | Where-Object { $_ -ne '' } | Select-Object -First 2
$SUBNET_STRING = $SUBNET_ARRAY -join ","

aws ecs create-service --cluster "$PROJECT_NAME-cluster" --service-name "$PROJECT_NAME-api" --task-definition "$PROJECT_NAME-api" --desired-count 1 --launch-type FARGATE --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_STRING],securityGroups=[$ECS_SG_ID],assignPublicIp=ENABLED}" --load-balancers "targetGroupArn=$TG_ARN,containerName=$PROJECT_NAME-api,containerPort=8000" --region $REGION

Write-Host "ECS service is being created. This may take a few minutes..." -ForegroundColor Yellow

# Update variables
$vars | Add-Member -NotePropertyName ALB_ARN -NotePropertyValue $ALB_ARN -Force
$vars | Add-Member -NotePropertyName ALB_DNS -NotePropertyValue $ALB_DNS -Force
$vars | Add-Member -NotePropertyName TG_ARN -NotePropertyValue $TG_ARN -Force
$vars | ConvertTo-Json | Out-File -FilePath "aws-deployment-vars.json" -Encoding UTF8

Write-Host "`nNext: Wait 2-3 minutes, then run .\scripts\deployment\deploy-aws-step4.ps1 to test and continue" -ForegroundColor Cyan

