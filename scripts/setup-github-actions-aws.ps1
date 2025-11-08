# Setup AWS IAM Role for GitHub Actions OIDC
# This script creates an IAM role that GitHub Actions can assume using OIDC

param(
    [string]$GitHubOrg = "franciszver",
    [string]$GitHubRepo = "PennyGadget",
    [string]$Region = "us-east-1"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub Actions AWS OIDC Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ROLE_NAME = "GitHubActions-PennyGadget-Deploy"
$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text

Write-Host "Account ID: $ACCOUNT_ID" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Green
Write-Host "GitHub Repo: $GitHubOrg/$GitHubRepo" -ForegroundColor Green
Write-Host ""

# Step 1: Create trust policy for GitHub OIDC
Write-Host "Step 1: Creating trust policy..." -ForegroundColor Cyan

$TRUST_POLICY = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                Federated = "arn:aws:iam::$ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
            }
            Action = "sts:AssumeRoleWithWebIdentity"
            Condition = @{
                StringEquals = @{
                    "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
                }
                StringLike = @{
                    "token.actions.githubusercontent.com:sub" = "repo:${GitHubOrg}/${GitHubRepo}:*"
                }
            }
        }
    )
} | ConvertTo-Json -Depth 10

$TRUST_POLICY | Out-File -FilePath "github-actions-trust-policy.json" -Encoding UTF8
Write-Host "Trust policy saved to github-actions-trust-policy.json" -ForegroundColor Green
Write-Host ""

# Step 2: Create IAM role
Write-Host "Step 2: Creating IAM role..." -ForegroundColor Cyan

# Check if role exists
$EXISTING_ROLE = aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>$null

if ($LASTEXITCODE -eq 0 -and $EXISTING_ROLE) {
    Write-Host "Role already exists: $EXISTING_ROLE" -ForegroundColor Yellow
    Write-Host "Updating trust policy..." -ForegroundColor Yellow
    aws iam update-assume-role-policy --role-name $ROLE_NAME --policy-document file://github-actions-trust-policy.json
    $ROLE_ARN = $EXISTING_ROLE
} else {
    Write-Host "Creating new role..." -ForegroundColor Green
    $ROLE_ARN = aws iam create-role `
        --role-name $ROLE_NAME `
        --assume-role-policy-document file://github-actions-trust-policy.json `
        --description "IAM role for GitHub Actions to deploy PennyGadget" `
        --query 'Role.Arn' `
        --output text
    
    Write-Host "Role created: $ROLE_ARN" -ForegroundColor Green
}

Write-Host ""

# Step 3: Attach policies for ECS deployment
Write-Host "Step 3: Attaching policies..." -ForegroundColor Cyan

$POLICIES = @(
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess",
    "arn:aws:iam::aws:policy/AmazonECS_FullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/CloudFrontFullAccess"
)

foreach ($POLICY in $POLICIES) {
    Write-Host "Attaching policy: $POLICY" -ForegroundColor Yellow
    aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn $POLICY 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Policy attached" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Policy may already be attached" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 4: Set up GitHub OIDC provider (if not exists)
Write-Host "Step 4: Setting up GitHub OIDC provider..." -ForegroundColor Cyan

$OIDC_PROVIDER = "arn:aws:iam::$ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"

$EXISTING_PROVIDER = aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?Arn==\`"$OIDC_PROVIDER\`"].Arn" --output text 2>$null

if ([string]::IsNullOrWhiteSpace($EXISTING_PROVIDER)) {
    Write-Host "Creating OIDC provider..." -ForegroundColor Yellow
    aws iam create-open-id-connect-provider `
        --url https://token.actions.githubusercontent.com `
        --client-id-list sts.amazonaws.com `
        --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 1c58a3a8518e8759bf075b76b750d4f2df2f2567 `
        2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ OIDC provider created" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ OIDC provider may already exist or creation failed" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✓ OIDC provider already exists" -ForegroundColor Green
}

Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Add this role ARN as a GitHub secret:" -ForegroundColor Cyan
Write-Host "   Name: AWS_ROLE_ARN" -ForegroundColor White
Write-Host "   Value: $ROLE_ARN" -ForegroundColor White
Write-Host ""
Write-Host "2. Go to: https://github.com/$GitHubOrg/$GitHubRepo/settings/secrets/actions" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Click 'New repository secret'" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Add the secret:" -ForegroundColor Cyan
Write-Host "   Name: AWS_ROLE_ARN" -ForegroundColor White
Write-Host "   Value: $ROLE_ARN" -ForegroundColor White
Write-Host ""
Write-Host "5. Push a new tag to trigger deployment:" -ForegroundColor Cyan
$tagCmd = "   git tag -a v1.1.1 -m 'Test deployment'"
$pushCmd = "   git push origin v1.1.1"
Write-Host $tagCmd -ForegroundColor White
Write-Host $pushCmd -ForegroundColor White
Write-Host ""

