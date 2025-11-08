# AWS Infrastructure Setup Script (PowerShell)
# Run with: .\scripts\setup_aws_infrastructure.ps1 -Profile your-profile-name

param(
    [string]$Profile = "",
    [string]$Region = "us-east-1",
    [string]$Environment = "development"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "AI Study Companion - AWS Infrastructure Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Region: $Region"
Write-Host "Environment: $Environment"
Write-Host ""

# Set AWS profile if provided
if ($Profile) {
    $env:AWS_PROFILE = $Profile
    Write-Host "Using AWS profile: $Profile" -ForegroundColor Green
}

# Generate random suffix for resource names
$RandomSuffix = -join ((48..57) + (97..122) | Get-Random -Count 4 | ForEach-Object {[char]$_})
$StackName = "pennygadget-$Environment-$RandomSuffix"

Write-Host "Stack name: $StackName"
Write-Host ""

# ============================================================================
# Step 1: Create RDS PostgreSQL Database
# ============================================================================
Write-Host "Step 1: Creating RDS PostgreSQL database..." -ForegroundColor Yellow

$DBInstanceId = "pennygadget-db-$Environment"
$DBName = "pennygadget"
$DBUser = "pgadmin"  # Changed from "admin" - "admin" is a reserved word in PostgreSQL
$DBPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Check if DB instance already exists
$ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }

try {
    $CheckDBCommand = "aws rds describe-db-instances --db-instance-identifier $DBInstanceId --region $Region"
    if ($ProfileArg) {
        $CheckDBCommand += " $ProfileArg"
    }
    $ExistingDB = Invoke-Expression $CheckDBCommand 2>$null
    if ($ExistingDB) {
        Write-Host "  [WARNING] RDS instance already exists: $DBInstanceId" -ForegroundColor Yellow
        Write-Host "  Getting existing endpoint..."
        $GetEndpointCommand = "aws rds describe-db-instances --db-instance-identifier $DBInstanceId --region $Region --query 'DBInstances[0].Endpoint.Address' --output text"
        if ($ProfileArg) {
            $GetEndpointCommand += " $ProfileArg"
        }
        $DBEndpoint = (Invoke-Expression $GetEndpointCommand).Trim()
    } else {
        throw "Not found"
    }
} catch {
    Write-Host "  Creating RDS PostgreSQL instance..." -ForegroundColor Green
    
    $ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }
    
    # Use PostgreSQL 17.6 (known to be available)
    # If you need a different version, you can modify this
    $PGVersion = "17.6"
    Write-Host "  Using PostgreSQL version: $PGVersion" -ForegroundColor Green
    
    # Optional: Verify version is available (uncomment if needed)
    # $CheckCommand = "aws rds describe-db-engine-versions --engine postgres --engine-version $PGVersion --region $Region"
    # if ($ProfileArg) { $CheckCommand += " $ProfileArg" }
    # $CheckResult = Invoke-Expression $CheckCommand 2>$null
    # if (-not $CheckResult) {
    #     Write-Host "  [WARNING] Version $PGVersion may not be available, trying 15.9..." -ForegroundColor Yellow
    #     $PGVersion = "15.9"
    # }
    
    Write-Host "  Creating RDS instance..." -ForegroundColor Green
    
    # Build command arguments
    $CreateArgs = @(
        "rds", "create-db-instance",
        "--db-instance-identifier", $DBInstanceId,
        "--db-instance-class", "db.t3.micro",
        "--engine", "postgres",
        "--engine-version", $PGVersion,
        "--master-username", $DBUser,
        "--master-user-password", $DBPassword,
        "--allocated-storage", "20",
        "--storage-type", "gp2",
        "--db-name", $DBName,
        "--backup-retention-period", "7",
        "--region", $Region,
        "--publicly-accessible",
        "--storage-encrypted",
        "--profile", $Profile
    )
    
    # Execute command
    $ErrorActionPreference = "Continue"
    $CreateOutput = & aws @CreateArgs 2>&1
    $ExitCode = $LASTEXITCODE
    
    # Check if command succeeded
    if ($ExitCode -eq 0) {
        Write-Host "  [OK] RDS instance creation initiated successfully" -ForegroundColor Green
        if ($CreateOutput) {
            # Try to parse JSON response
            try {
                $JsonOutput = $CreateOutput | ConvertFrom-Json
                Write-Host "  Database ID: $($JsonOutput.DBInstance.DBInstanceIdentifier)" -ForegroundColor Gray
                Write-Host "  Status: $($JsonOutput.DBInstance.DBInstanceStatus)" -ForegroundColor Gray
            } catch {
                Write-Host "  Response received (checking status...)" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  [ERROR] Failed to create RDS instance (Exit code: $ExitCode)" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Full error output:" -ForegroundColor Red
        Write-Host "  ==================" -ForegroundColor Red
        
        # Display all error output
        foreach ($line in $CreateOutput) {
            if ($line -is [System.Management.Automation.ErrorRecord]) {
                Write-Host "  $($line.Exception.Message)" -ForegroundColor Red
                if ($line.Exception.InnerException) {
                    Write-Host "  Inner: $($line.Exception.InnerException.Message)" -ForegroundColor Red
                }
            } else {
                Write-Host "  $line" -ForegroundColor Red
            }
        }
        
        Write-Host ""
        Write-Host "  Common issues and solutions:" -ForegroundColor Yellow
        Write-Host "  ============================" -ForegroundColor Yellow
        Write-Host "  1. Insufficient permissions:" -ForegroundColor Yellow
        Write-Host "     - Your AWS user needs 'rds:CreateDBInstance' permission" -ForegroundColor Yellow
        Write-Host "     - Check IAM policies for your user/role" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  2. RDS quota exceeded:" -ForegroundColor Yellow
        Write-Host "     - Check: aws service-quotas get-service-quota --service-code rds --quota-code L-7B6409FD" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  3. PostgreSQL version not available:" -ForegroundColor Yellow
        Write-Host "     - Check: aws rds describe-db-engine-versions --engine postgres --region $Region" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  4. DB instance already exists:" -ForegroundColor Yellow
        Write-Host "     - Check: aws rds describe-db-instances --db-instance-identifier $DBInstanceId --region $Region --profile $Profile" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  5. Invalid parameter combination:" -ForegroundColor Yellow
        Write-Host "     - Some parameters may not be compatible in your region" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Next steps:" -ForegroundColor Cyan
        Write-Host "  - Check AWS Console: RDS -> Databases" -ForegroundColor Cyan
        Write-Host "  - Review the error message above for specific details" -ForegroundColor Cyan
        Write-Host "  - Try running the command manually to see full error:" -ForegroundColor Cyan
        Write-Host "    aws rds create-db-instance --db-instance-identifier $DBInstanceId --db-instance-class db.t3.micro --engine postgres --engine-version $PGVersion --master-username $DBUser --master-user-password 'PASSWORD' --allocated-storage 20 --storage-type gp2 --db-name $DBName --backup-retention-period 7 --region $Region --publicly-accessible --storage-encrypted --profile $Profile" -ForegroundColor Gray
        
        exit 1
    }
    
    Write-Host "  [WAIT] Waiting for database to be available (this may take 5-10 minutes)..." -ForegroundColor Yellow
    Write-Host "  You can check status in AWS Console: RDS -> Databases -> $DBInstanceId" -ForegroundColor Gray
    
    try {
        $WaitArgs = @(
            "rds", "wait", "db-instance-available",
            "--db-instance-identifier", $DBInstanceId,
            "--region", $Region,
            "--profile", $Profile
        )
        
        & aws @WaitArgs 2>&1 | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [WARNING] Wait command failed, but database may still be creating..." -ForegroundColor Yellow
            Write-Host "  Check AWS Console for actual status" -ForegroundColor Yellow
        } else {
            Write-Host "  [OK] Database is now available" -ForegroundColor Green
        }
    } catch {
        Write-Host "  [WARNING] Could not wait for database. It may still be creating." -ForegroundColor Yellow
        Write-Host "  Error: $_" -ForegroundColor Yellow
        Write-Host "  Check AWS Console: RDS -> Databases" -ForegroundColor Yellow
    }
    
    # Get database endpoint
    try {
        $DescribeArgs = @(
            "rds", "describe-db-instances",
            "--db-instance-identifier", $DBInstanceId,
            "--region", $Region,
            "--query", "DBInstances[0].Endpoint.Address",
            "--output", "text",
            "--profile", $Profile
        )
        
        $DBEndpointResult = & aws @DescribeArgs 2>&1
        
        if ($LASTEXITCODE -eq 0 -and $DBEndpointResult -and $DBEndpointResult -notmatch "error|Error|ERROR|None|null|NotFound") {
            $DBEndpoint = $DBEndpointResult.ToString().Trim()
        } else {
            Write-Host "  [WARNING] Could not get database endpoint yet. Database may still be creating." -ForegroundColor Yellow
            Write-Host "  Response: $DBEndpointResult" -ForegroundColor Yellow
            Write-Host "  Check AWS console: RDS -> Databases -> $DBInstanceId" -ForegroundColor Yellow
            $DBEndpoint = "pending-creation"
        }
    } catch {
        Write-Host "  [WARNING] Exception getting endpoint: $_" -ForegroundColor Yellow
        $DBEndpoint = "pending-creation"
    }
}

Write-Host "  [OK] Database created: $DBEndpoint" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 2: Create Cognito User Pool
# ============================================================================
Write-Host "Step 2: Creating Cognito User Pool..." -ForegroundColor Yellow

$UserPoolName = "pennygadget-users-$Environment"

# Check if user pool already exists
$ListPoolsCommand = "aws cognito-idp list-user-pools --max-results 60 --region $Region --output json"
if ($ProfileArg) {
    $ListPoolsCommand += " $ProfileArg"
}
$ExistingPools = Invoke-Expression $ListPoolsCommand | ConvertFrom-Json
$ExistingPool = $ExistingPools.UserPools | Where-Object { $_.Name -eq $UserPoolName }

if ($ExistingPool) {
    Write-Host "  [WARNING] User pool already exists: $($ExistingPool.Id)" -ForegroundColor Yellow
    $UserPoolId = $ExistingPool.Id
} else {
    Write-Host "  Creating Cognito User Pool..." -ForegroundColor Green
    
    $ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }
    
    $CreatePoolCommand = "aws cognito-idp create-user-pool " +
        "--pool-name '$UserPoolName' " +
        "--policies 'PasswordPolicy={MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=true}' " +
        "--auto-verified-attributes email " +
        "--region $Region " +
        "--query 'UserPool.Id' " +
        "--output text"
    
    if ($ProfileArg) {
        $CreatePoolCommand += " $ProfileArg"
    }
    
    $UserPoolId = (Invoke-Expression $CreatePoolCommand).Trim()
    
    Write-Host "  [OK] User Pool created: $UserPoolId" -ForegroundColor Green
}

# Create User Pool Client
$ClientName = "pennygadget-client-$Environment"

$ListClientsCommand = "aws cognito-idp list-user-pool-clients --user-pool-id '$UserPoolId' --region $Region --output json"
if ($ProfileArg) {
    $ListClientsCommand += " $ProfileArg"
}
$ExistingClients = Invoke-Expression $ListClientsCommand | ConvertFrom-Json
$ExistingClient = $ExistingClients.UserPoolClients | Where-Object { $_.ClientName -eq $ClientName }

if ($ExistingClient) {
    Write-Host "  [WARNING] User pool client already exists: $($ExistingClient.ClientId)" -ForegroundColor Yellow
    $ClientId = $ExistingClient.ClientId
    
    # Update existing client to include USER_SRP_AUTH
    Write-Host "  Updating client to enable USER_SRP_AUTH..." -ForegroundColor Green
    $ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }
    
    $UpdateClientCommand = "aws cognito-idp update-user-pool-client " +
        "--user-pool-id '$UserPoolId' " +
        "--client-id '$ClientId' " +
        "--explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH " +
        "--region $Region " +
        "--output json"
    
    if ($ProfileArg) {
        $UpdateClientCommand += " $ProfileArg"
    }
    
    try {
        Invoke-Expression $UpdateClientCommand | Out-Null
        Write-Host "  [OK] Client updated successfully" -ForegroundColor Green
    } catch {
        Write-Host "  [WARNING] Failed to update client: $_" -ForegroundColor Yellow
        Write-Host "  You may need to manually update the client to enable USER_SRP_AUTH" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Creating User Pool Client..." -ForegroundColor Green
    
    $ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }
    
    $CreateClientCommand = "aws cognito-idp create-user-pool-client " +
        "--user-pool-id '$UserPoolId' " +
        "--client-name '$ClientName' " +
        "--generate-secret " +
        "--explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH " +
        "--region $Region " +
        "--query 'UserPoolClient.ClientId' " +
        "--output text"
    
    if ($ProfileArg) {
        $CreateClientCommand += " $ProfileArg"
    }
    
    $ClientId = (Invoke-Expression $CreateClientCommand).Trim()
    
    Write-Host "  [OK] User Pool Client created: $ClientId" -ForegroundColor Green
}

# Create User Groups (roles)
Write-Host "  Creating user groups (roles)..." -ForegroundColor Green
$Roles = @("student", "tutor", "parent", "admin")
foreach ($Role in $Roles) {
    $GroupName = "$Role" + "s"
    $ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }
    
    try {
        $CheckGroupCommand = "aws cognito-idp get-group --user-pool-id '$UserPoolId' --group-name '$GroupName' --region $Region"
        if ($ProfileArg) {
            $CheckGroupCommand += " $ProfileArg"
        }
        Invoke-Expression $CheckGroupCommand 2>$null | Out-Null
        Write-Host "    [WARNING] Group already exists: $GroupName" -ForegroundColor Yellow
    } catch {
        $CreateGroupCommand = "aws cognito-idp create-group " +
            "--user-pool-id '$UserPoolId' " +
            "--group-name '$GroupName' " +
            "--description 'Users with $Role role' " +
            "--region $Region"
        if ($ProfileArg) {
            $CreateGroupCommand += " $ProfileArg"
        }
        Invoke-Expression $CreateGroupCommand | Out-Null
        Write-Host "    [OK] Created group: $GroupName" -ForegroundColor Green
    }
}

Write-Host ""

# ============================================================================
# Step 3: Configure SES (Simple Email Service)
# ============================================================================
Write-Host "Step 3: Configuring SES for email..." -ForegroundColor Yellow

try {
    $ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }
    $SESCommand = "aws ses get-account-sending-enabled --region $Region --query 'Enabled' --output text"
    if ($ProfileArg) {
        $SESCommand += " $ProfileArg"
    }
    $SESEnabled = (Invoke-Expression $SESCommand 2>$null).Trim()
    if ($SESEnabled -eq "false") {
        Write-Host "  [WARNING] SES is in sandbox mode. You'll need to:" -ForegroundColor Yellow
        Write-Host "     1. Verify your email address: aws ses verify-email-identity --email-address your@email.com --region $Region" -ForegroundColor Yellow
        Write-Host "     2. Request production access: https://console.aws.amazon.com/ses/home?region=$Region#/account/settings" -ForegroundColor Yellow
    } else {
        Write-Host "  [OK] SES is enabled" -ForegroundColor Green
    }
} catch {
    Write-Host "  [WARNING] Could not check SES status" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# Step 4: Create S3 Bucket for Transcripts (Optional)
# ============================================================================
Write-Host "Step 4: Creating S3 bucket for transcripts..." -ForegroundColor Yellow

$BucketName = "pennygadget-transcripts-$Environment-$RandomSuffix"

$ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }

try {
    $CheckBucketCommand = "aws s3 ls 's3://$BucketName'"
    if ($ProfileArg) {
        $CheckBucketCommand += " $ProfileArg"
    }
    Invoke-Expression $CheckBucketCommand 2>$null | Out-Null
    Write-Host "  [WARNING] S3 bucket already exists: $BucketName" -ForegroundColor Yellow
} catch {
    $CreateBucketCommand = "aws s3 mb 's3://$BucketName'"
    if ($Region -ne "us-east-1") {
        $CreateBucketCommand += " --region $Region"
    }
    if ($ProfileArg) {
        $CreateBucketCommand += " $ProfileArg"
    }
    Invoke-Expression $CreateBucketCommand | Out-Null
    
    # Enable versioning
    $VersioningConfig = '{"Status":"Enabled"}'
    
    $VersioningCommand = "aws s3api put-bucket-versioning " +
        "--bucket '$BucketName' " +
        "--versioning-configuration '$VersioningConfig'"
    if ($Region -ne "us-east-1") {
        $VersioningCommand += " --region $Region"
    }
    if ($ProfileArg) {
        $VersioningCommand += " $ProfileArg"
    }
    Invoke-Expression $VersioningCommand | Out-Null
    
    Write-Host "  [OK] S3 bucket created: $BucketName" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 5: Save Configuration
# ============================================================================
Write-Host "Step 5: Saving configuration..." -ForegroundColor Yellow

$ConfigFile = ".aws-config-$Environment.env"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$ConfigContent = @"
# AWS Infrastructure Configuration
# Generated: $Timestamp
# Environment: $Environment
# Region: $Region

# Database (RDS PostgreSQL)
DB_HOST=$DBEndpoint
DB_PORT=5432
DB_NAME=$DBName
DB_USER=$DBUser
DB_PASSWORD=$DBPassword

# Cognito
COGNITO_USER_POOL_ID=$UserPoolId
COGNITO_CLIENT_ID=$ClientId
COGNITO_REGION=$Region

# SES
SES_REGION=$Region
SES_FROM_EMAIL=noreply@yourdomain.com

# S3
S3_BUCKET_NAME=$BucketName
S3_REGION=$Region

# AWS Region
AWS_REGION=$Region
"@

$ConfigContent | Out-File -FilePath $ConfigFile -Encoding UTF8

Write-Host "  [OK] Configuration saved to: $ConfigFile" -ForegroundColor Green
Write-Host "  [IMPORTANT] Add these values to your .env file!" -ForegroundColor Yellow
Write-Host "  [IMPORTANT] Keep DB_PASSWORD secure!" -ForegroundColor Yellow
Write-Host ""

# ============================================================================
# Summary
# ============================================================================
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Infrastructure Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Resources created:"
Write-Host "  RDS Database: $DBEndpoint" -ForegroundColor Cyan
Write-Host "  Cognito User Pool: $UserPoolId" -ForegroundColor Cyan
Write-Host "  SES: Configured (may need verification)" -ForegroundColor Cyan
Write-Host "  S3 Bucket: $BucketName" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Copy values from $ConfigFile to your .env file" -ForegroundColor Yellow
Write-Host "  2. Run database migrations: python scripts/setup_db.py" -ForegroundColor Yellow
Write-Host "  3. Verify SES email: aws ses verify-email-identity --email-address your@email.com --region $Region" -ForegroundColor Yellow
Write-Host "  4. Test connection to database" -ForegroundColor Yellow
Write-Host ""
Write-Host "[SECURITY NOTES]:" -ForegroundColor Red
Write-Host "  - Database password is in $ConfigFile (keep secure!)" -ForegroundColor Red
Write-Host "  - RDS instance is publicly accessible (restrict in production)" -ForegroundColor Red
Write-Host "  - Add security groups to restrict database access" -ForegroundColor Red
Write-Host ""

