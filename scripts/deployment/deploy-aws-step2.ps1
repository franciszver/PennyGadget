# AWS Deployment - Step 2: Continue after RDS is ready
# Load variables from previous step
$vars = Get-Content "aws-deployment-vars.json" | ConvertFrom-Json

$ACCOUNT_ID = $vars.ACCOUNT_ID
$REGION = $vars.REGION
$PROJECT_NAME = $vars.PROJECT_NAME
$VPC_ID = $vars.VPC_ID
$SUBNETS = $vars.SUBNETS
$RDS_SG_ID = $vars.RDS_SG_ID
$ECS_SG_ID = $vars.ECS_SG_ID
$DB_PASSWORD = $vars.DB_PASSWORD
$DB_INSTANCE_ID = $vars.DB_INSTANCE_ID

# Check RDS status
Write-Host "Checking RDS database status..." -ForegroundColor Cyan
$DB_STATUS = aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --query 'DBInstances[0].DBInstanceStatus' --output text --region $REGION
Write-Host "Database Status: $DB_STATUS" -ForegroundColor $(if ($DB_STATUS -eq "available") { "Green" } else { "Yellow" })

if ($DB_STATUS -ne "available") {
    Write-Host "Database is not ready yet. Please wait and run this script again." -ForegroundColor Yellow
    exit
}

# Get database endpoint
$DB_ENDPOINT = aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --query 'DBInstances[0].Endpoint.Address' --output text --region $REGION
Write-Host "Database Endpoint: $DB_ENDPOINT" -ForegroundColor Green

# Step 6: Update Security Groups - Allow ECS to Access RDS
Write-Host "`nStep 6: Updating security groups..." -ForegroundColor Cyan
aws ec2 authorize-security-group-ingress --group-id $RDS_SG_ID --protocol tcp --port 5432 --source-group $ECS_SG_ID --region $REGION
Write-Host "Security groups updated. ECS can now access RDS." -ForegroundColor Green

# Step 7: Create ECR Repository
Write-Host "`nStep 7: Creating ECR repository..." -ForegroundColor Cyan
aws ecr create-repository --repository-name "$PROJECT_NAME-api" --image-scanning-configuration scanOnPush=true --region $REGION 2>$null
$ECR_REPO_URI = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME-api"
Write-Host "ECR Repository URI: $ECR_REPO_URI" -ForegroundColor Green

# Step 8: Login to ECR and Build Docker Image
Write-Host "`nStep 8: Building and pushing Docker image..." -ForegroundColor Cyan
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO_URI

Write-Host "Building Docker image..." -ForegroundColor Yellow
docker build -t "$PROJECT_NAME-api" .

Write-Host "Tagging image..." -ForegroundColor Yellow
docker tag "$PROJECT_NAME-api:latest" "$ECR_REPO_URI:latest"

Write-Host "Pushing to ECR..." -ForegroundColor Yellow
docker push "$ECR_REPO_URI:latest"

Write-Host "Docker image pushed successfully!" -ForegroundColor Green

# Step 9: Create IAM Role for ECS Tasks
Write-Host "`nStep 9: Creating IAM role..." -ForegroundColor Cyan
$ECS_TASK_ROLE_NAME = "$PROJECT_NAME-ecs-task-role"

# Check if role already exists
$EXISTING_ROLE = aws iam get-role --role-name $ECS_TASK_ROLE_NAME --query 'Role.Arn' --output text 2>$null
if ($LASTEXITCODE -eq 0 -and $EXISTING_ROLE) {
    Write-Host "IAM role already exists: $EXISTING_ROLE" -ForegroundColor Yellow
    $ECS_TASK_ROLE_ARN = $EXISTING_ROLE
} else {
    $TRUST_POLICY = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Allow"
                Principal = @{
                    Service = "ecs-tasks.amazonaws.com"
                }
                Action = "sts:AssumeRole"
            }
        )
    } | ConvertTo-Json -Compress

    aws iam create-role --role-name $ECS_TASK_ROLE_NAME --assume-role-policy-document $TRUST_POLICY 2>$null
    if ($LASTEXITCODE -eq 0) {
        aws iam attach-role-policy --role-name $ECS_TASK_ROLE_NAME --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy 2>$null
        $ECS_TASK_ROLE_ARN = aws iam get-role --role-name $ECS_TASK_ROLE_NAME --query 'Role.Arn' --output text
        Write-Host "Created IAM role: $ECS_TASK_ROLE_ARN" -ForegroundColor Green
    } else {
        Write-Host "Failed to create IAM role. Please check AWS permissions." -ForegroundColor Red
        exit 1
    }
}
Write-Host "ECS Task Role ARN: $ECS_TASK_ROLE_ARN" -ForegroundColor Green

# Step 10: Create ECS Cluster
Write-Host "`nStep 10: Creating ECS cluster..." -ForegroundColor Cyan
aws ecs create-cluster --cluster-name "$PROJECT_NAME-cluster" --region $REGION 2>$null
Write-Host "ECS cluster created: $PROJECT_NAME-cluster" -ForegroundColor Green

# Step 12: Create CloudWatch Log Group
Write-Host "`nStep 12: Creating CloudWatch log group..." -ForegroundColor Cyan
aws logs create-log-group --log-group-name "/ecs/$PROJECT_NAME-api" --region $REGION 2>$null
Write-Host "CloudWatch log group created!" -ForegroundColor Green

# Update variables file
$vars | Add-Member -NotePropertyName DB_ENDPOINT -NotePropertyValue $DB_ENDPOINT -Force
$vars | Add-Member -NotePropertyName ECR_REPO_URI -NotePropertyValue $ECR_REPO_URI -Force
$vars | Add-Member -NotePropertyName ECS_TASK_ROLE_ARN -NotePropertyValue $ECS_TASK_ROLE_ARN -Force
$vars | ConvertTo-Json | Out-File -FilePath "aws-deployment-vars.json" -Encoding UTF8

Write-Host "`nNext: Run .\scripts\deployment\deploy-aws-step3.ps1 to create task definition and deploy service" -ForegroundColor Cyan

