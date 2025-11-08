# Fix Cognito Client - Enable USER_SRP_AUTH
# This script updates an existing Cognito User Pool Client to enable USER_SRP_AUTH
# which is required by amazon-cognito-identity-js for authentication

param(
    [string]$UserPoolId = "",
    [string]$ClientId = "",
    [string]$Region = "us-east-1",
    [string]$Profile = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix Cognito Client - Enable USER_SRP_AUTH" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is installed
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: AWS CLI is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Try to get values from environment variables or aws-deployment-vars.json if not provided
if (-not $UserPoolId) {
    $UserPoolId = $env:COGNITO_USER_POOL_ID
}
if (-not $ClientId) {
    $ClientId = $env:COGNITO_CLIENT_ID
}

if (-not $UserPoolId -or -not $ClientId) {
    if (Test-Path "aws-deployment-vars.json") {
        Write-Host "Reading configuration from aws-deployment-vars.json..." -ForegroundColor Green
        $config = Get-Content "aws-deployment-vars.json" | ConvertFrom-Json
        
        if (-not $UserPoolId) {
            $UserPoolId = $config.COGNITO_USER_POOL_ID
        }
        if (-not $ClientId) {
            $ClientId = $config.COGNITO_CLIENT_ID
        }
        if (-not $Region -or $Region -eq "us-east-1") {
            $Region = $config.REGION
        }
    }
}

# If still not found, try to list user pools to help user find it
if (-not $UserPoolId) {
    Write-Host "User Pool ID not found. Listing available User Pools..." -ForegroundColor Yellow
    Write-Host ""
    $ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }
    $ListPoolsCommand = "aws cognito-idp list-user-pools --max-results 60 --region $Region --output json"
    if ($ProfileArg) {
        $ListPoolsCommand += " $ProfileArg"
    }
    
    try {
        $Pools = Invoke-Expression $ListPoolsCommand | ConvertFrom-Json
        if ($Pools.UserPools.Count -gt 0) {
            Write-Host "Available User Pools:" -ForegroundColor Cyan
            $Pools.UserPools | ForEach-Object {
                Write-Host "  - $($_.Name): $($_.Id)" -ForegroundColor White
            }
            Write-Host ""
        }
    } catch {
        Write-Host "  Could not list user pools: $_" -ForegroundColor Yellow
    }
}

# Validate required parameters
if (-not $UserPoolId) {
    Write-Host "ERROR: User Pool ID is required" -ForegroundColor Red
    Write-Host "Usage: .\fix-cognito-client.ps1 -UserPoolId <pool-id> -ClientId <client-id> [-Region <region>] [-Profile <profile>]" -ForegroundColor Yellow
    exit 1
}

if (-not $ClientId) {
    Write-Host "ERROR: Client ID is required" -ForegroundColor Red
    Write-Host "Usage: .\fix-cognito-client.ps1 -UserPoolId <pool-id> -ClientId <client-id> [-Region <region>] [-Profile <profile>]" -ForegroundColor Yellow
    exit 1
}

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  User Pool ID: $UserPoolId"
Write-Host "  Client ID: $ClientId"
Write-Host "  Region: $Region"
if ($Profile) {
    Write-Host "  Profile: $Profile"
}
Write-Host ""

# Build AWS CLI command
$ProfileArg = if ($Profile) { "--profile $Profile" } else { "" }

# First, get the current client configuration to preserve other settings
Write-Host "Fetching current client configuration..." -ForegroundColor Green
$GetClientCommand = "aws cognito-idp describe-user-pool-client --user-pool-id '$UserPoolId' --client-id '$ClientId' --region $Region --output json"
if ($ProfileArg) {
    $GetClientCommand += " $ProfileArg"
}

try {
    $ClientConfig = Invoke-Expression $GetClientCommand | ConvertFrom-Json
    Write-Host "  [OK] Current client configuration retrieved" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Failed to retrieve client configuration: $_" -ForegroundColor Red
    exit 1
}

# Update the client with USER_SRP_AUTH enabled
Write-Host ""
Write-Host "Updating client to enable USER_SRP_AUTH..." -ForegroundColor Green

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
    $Result = Invoke-Expression $UpdateClientCommand | ConvertFrom-Json
    Write-Host "  [OK] Client updated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Updated authentication flows:" -ForegroundColor Cyan
    $Result.UserPoolClient.ExplicitAuthFlows | ForEach-Object {
        Write-Host "  - $_" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Fix Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "The Cognito client now supports USER_SRP_AUTH." -ForegroundColor Green
    Write-Host "Users should now be able to log in successfully." -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Failed to update client: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "You may need to manually update the client in the AWS Console:" -ForegroundColor Yellow
    Write-Host "  1. Go to AWS Cognito Console" -ForegroundColor Yellow
    Write-Host "  2. Select your User Pool" -ForegroundColor Yellow
    Write-Host "  3. Go to App integration > App clients" -ForegroundColor Yellow
    Write-Host "  4. Edit your client" -ForegroundColor Yellow
    Write-Host "  5. Enable 'ALLOW_USER_SRP_AUTH' in Authentication flows" -ForegroundColor Yellow
    exit 1
}

