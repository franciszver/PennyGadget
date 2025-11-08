# AWS Production Deployment Script for ElevareAI
# Execute this script step by step, or run individual sections

# Step 1: Get AWS Account ID and Set Variables
Write-Host "Step 1: Setting up variables..." -ForegroundColor Cyan
$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
$REGION = "us-east-1"
$PROJECT_NAME = "elevareai"

Write-Host "Account ID: $ACCOUNT_ID" -ForegroundColor Green
Write-Host "Region: $REGION" -ForegroundColor Green
Write-Host "Project: $PROJECT_NAME" -ForegroundColor Green

# Step 2: Get Default VPC and Subnets
Write-Host "`nStep 2: Getting VPC and subnets..." -ForegroundColor Cyan
$VPC_ID = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region $REGION
$SUBNETS = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[?MapPublicIpOnLaunch==`"true`"].SubnetId" --output text --region $REGION

Write-Host "VPC ID: $VPC_ID" -ForegroundColor Green
Write-Host "Subnets: $SUBNETS" -ForegroundColor Green

# Step 3: Create or Get Security Group for RDS
Write-Host "`nStep 3: Creating/getting RDS security group..." -ForegroundColor Cyan
$RDS_SG_NAME = "$PROJECT_NAME-rds-sg"
$RDS_SG_ID = aws ec2 describe-security-groups --filters "Name=group-name,Values=$RDS_SG_NAME" "Name=vpc-id,Values=$VPC_ID" --query 'SecurityGroups[0].GroupId' --output text --region $REGION

if ([string]::IsNullOrWhiteSpace($RDS_SG_ID)) {
    $RDS_SG_ID = aws ec2 create-security-group --group-name $RDS_SG_NAME --description "Security group for ElevareAI RDS database" --vpc-id $VPC_ID --region $REGION --query 'GroupId' --output text
    Write-Host "Created RDS Security Group ID: $RDS_SG_ID" -ForegroundColor Green
} else {
    Write-Host "Using existing RDS Security Group ID: $RDS_SG_ID" -ForegroundColor Yellow
}

# Step 4: Create or Get Security Group for ECS/ALB
Write-Host "`nStep 4: Creating/getting ECS security group..." -ForegroundColor Cyan
$ECS_SG_NAME = "$PROJECT_NAME-ecs-sg"
$ECS_SG_ID = aws ec2 describe-security-groups --filters "Name=group-name,Values=$ECS_SG_NAME" "Name=vpc-id,Values=$VPC_ID" --query 'SecurityGroups[0].GroupId' --output text --region $REGION

if ([string]::IsNullOrWhiteSpace($ECS_SG_ID)) {
    $ECS_SG_ID = aws ec2 create-security-group --group-name $ECS_SG_NAME --description "Security group for ElevareAI ECS tasks and ALB" --vpc-id $VPC_ID --region $REGION --query 'GroupId' --output text
    Write-Host "Created ECS Security Group ID: $ECS_SG_ID" -ForegroundColor Green
} else {
    Write-Host "Using existing ECS Security Group ID: $ECS_SG_ID" -ForegroundColor Yellow
}

# Allow HTTP/HTTPS from internet (idempotent - will fail silently if already exists)
Write-Host "Adding security group rules..." -ForegroundColor Cyan
aws ec2 authorize-security-group-ingress --group-id $ECS_SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $REGION 2>$null
aws ec2 authorize-security-group-ingress --group-id $ECS_SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $REGION 2>$null
Write-Host "ECS Security Group rules configured" -ForegroundColor Green

# Step 5: Create RDS PostgreSQL Database
Write-Host "`nStep 5: Creating RDS database..." -ForegroundColor Cyan
$DB_PASSWORD = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object {[char]$_})
Write-Host "Generated DB Password: $DB_PASSWORD" -ForegroundColor Yellow
Write-Host "SAVE THIS PASSWORD! You'll need it later." -ForegroundColor Red

$DB_INSTANCE_ID = "$PROJECT_NAME-db"

# Check if RDS instance already exists
$EXISTING_DB = aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --region $REGION 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "RDS instance already exists. Skipping creation." -ForegroundColor Yellow
    $DB_ENDPOINT = aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --query 'DBInstances[0].Endpoint.Address' --output text --region $REGION
    Write-Host "Database Endpoint: $DB_ENDPOINT" -ForegroundColor Green
} else {
    # Use PostgreSQL 15.14 (latest stable 15.x version)
    Write-Host "Creating RDS PostgreSQL 15.14 instance..." -ForegroundColor Yellow
    aws rds create-db-instance --db-instance-identifier $DB_INSTANCE_ID --db-instance-class db.t3.micro --engine postgres --engine-version 15.14 --master-username elevareai_admin --master-user-password $DB_PASSWORD --allocated-storage 20 --storage-type gp2 --vpc-security-group-ids $RDS_SG_ID --db-name elevareai --backup-retention-period 7 --publicly-accessible --region $REGION
}

Write-Host "RDS database is being created. This will take 5-10 minutes..." -ForegroundColor Yellow
Write-Host "Database Password: $DB_PASSWORD" -ForegroundColor Red
Write-Host "Save this password now!" -ForegroundColor Red

# Save variables to file for later use
@{
    ACCOUNT_ID = $ACCOUNT_ID
    REGION = $REGION
    PROJECT_NAME = $PROJECT_NAME
    VPC_ID = $VPC_ID
    SUBNETS = $SUBNETS
    RDS_SG_ID = $RDS_SG_ID
    ECS_SG_ID = $ECS_SG_ID
    DB_PASSWORD = $DB_PASSWORD
    DB_INSTANCE_ID = $DB_INSTANCE_ID
} | ConvertTo-Json | Out-File -FilePath "aws-deployment-vars.json" -Encoding UTF8

# Step 6: Create Cognito User Pool and Client
Write-Host "`nStep 6: Creating Cognito User Pool..." -ForegroundColor Cyan
$COGNITO_POOL_NAME = "$PROJECT_NAME-users"
$COGNITO_CLIENT_NAME = "$PROJECT_NAME-client"

# Check if user pool already exists
$EXISTING_POOL = aws cognito-idp list-user-pools --max-results 10 --region $REGION --query "UserPools[?Name=='$COGNITO_POOL_NAME'].Id" --output text
if ($EXISTING_POOL) {
    Write-Host "Cognito User Pool already exists. Using existing pool: $EXISTING_POOL" -ForegroundColor Yellow
    $COGNITO_USER_POOL_ID = $EXISTING_POOL
} else {
    # Create User Pool
    $COGNITO_USER_POOL_ID = aws cognito-idp create-user-pool `
        --pool-name $COGNITO_POOL_NAME `
        --policies "PasswordPolicy={MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=true}" `
        --auto-verified-attributes email `
        --region $REGION `
        --query 'UserPool.Id' `
        --output text
    Write-Host "Created Cognito User Pool ID: $COGNITO_USER_POOL_ID" -ForegroundColor Green
}

# Check if client already exists
$EXISTING_CLIENT = aws cognito-idp list-user-pool-clients --user-pool-id $COGNITO_USER_POOL_ID --region $REGION --query "UserPoolClients[?ClientName=='$COGNITO_CLIENT_NAME'].ClientId" --output text
if ($EXISTING_CLIENT) {
    Write-Host "Cognito Client already exists. Using existing client: $EXISTING_CLIENT" -ForegroundColor Yellow
    $COGNITO_CLIENT_ID = $EXISTING_CLIENT
} else {
    # Create User Pool Client (PUBLIC - no secret for frontend JavaScript)
    $COGNITO_CLIENT_ID = aws cognito-idp create-user-pool-client `
        --user-pool-id $COGNITO_USER_POOL_ID `
        --client-name $COGNITO_CLIENT_NAME `
        --explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH `
        --region $REGION `
        --query 'UserPoolClient.ClientId' `
        --output text
    Write-Host "Created Cognito Client ID: $COGNITO_CLIENT_ID" -ForegroundColor Green
}

# Update variables file with Cognito IDs
$vars = Get-Content aws-deployment-vars.json | ConvertFrom-Json
$vars | Add-Member -NotePropertyName "COGNITO_USER_POOL_ID" -NotePropertyValue $COGNITO_USER_POOL_ID -Force
$vars | Add-Member -NotePropertyName "COGNITO_CLIENT_ID" -NotePropertyValue $COGNITO_CLIENT_ID -Force
$vars | ConvertTo-Json | Out-File -FilePath "aws-deployment-vars.json" -Encoding UTF8

Write-Host "Cognito User Pool ID: $COGNITO_USER_POOL_ID" -ForegroundColor Green
Write-Host "Cognito Client ID: $COGNITO_CLIENT_ID" -ForegroundColor Green

Write-Host "`nVariables saved to aws-deployment-vars.json" -ForegroundColor Green
Write-Host "`nNext: Wait 5-10 minutes for RDS to be available, then run .\scripts\deployment\deploy-aws-step2.ps1" -ForegroundColor Cyan

