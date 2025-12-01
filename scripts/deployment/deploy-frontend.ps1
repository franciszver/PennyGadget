# Deploy Frontend to S3 and CloudFront
# This script rebuilds the frontend with latest changes and deploys it

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Frontend Deployment Script" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Load deployment variables
if (-not (Test-Path "aws-deployment-vars.json")) {
    Write-Host "ERROR: aws-deployment-vars.json not found!" -ForegroundColor Red
    Write-Host "Please run the initial deployment script first." -ForegroundColor Red
    exit 1
}

$vars = Get-Content "aws-deployment-vars.json" | ConvertFrom-Json

# Set AWS profile
$env:AWS_PROFILE = "default1"

$REGION = $vars.REGION
$BUCKET_NAME = $vars.BUCKET_NAME
$ALB_DNS = $vars.ALB_DNS
$CF_DIST_ID = $vars.CF_DIST_ID

if (-not $BUCKET_NAME -or -not $CF_DIST_ID) {
    Write-Host "ERROR: Missing required variables in aws-deployment-vars.json!" -ForegroundColor Red
    Write-Host "Required: BUCKET_NAME, CF_DIST_ID" -ForegroundColor Red
    exit 1
}

# Get Cognito IDs (optional - frontend will use demo mode if not provided)
$COGNITO_USER_POOL_ID = if ($vars.COGNITO_USER_POOL_ID) { $vars.COGNITO_USER_POOL_ID } else { $env:COGNITO_USER_POOL_ID }
$COGNITO_CLIENT_ID = if ($vars.COGNITO_CLIENT_ID) { $vars.COGNITO_CLIENT_ID } else { $env:COGNITO_CLIENT_ID }

if (-not $COGNITO_USER_POOL_ID -or -not $COGNITO_CLIENT_ID) {
    Write-Host "WARNING: Cognito credentials not found!" -ForegroundColor Yellow
    Write-Host "Frontend will be built in development mode (demo accounts enabled)" -ForegroundColor Yellow
    Write-Host "For production Cognito, set COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID" -ForegroundColor Yellow
    Write-Host ""
}

# Check if ALB has HTTPS listener
$CheckHTTPSCommand = "aws elbv2 describe-listeners --load-balancer-arn '$($vars.ALB_ARN)' --region $REGION --query 'Listeners[?Port==`\`"443`\`"]' --output json"
$HTTPSListeners = Invoke-Expression $CheckHTTPSCommand | ConvertFrom-Json
$UseHTTPS = $HTTPSListeners.Count -gt 0

$API_PROTOCOL = if ($UseHTTPS) { "https" } else { "http" }
$API_URL = "${API_PROTOCOL}://${ALB_DNS}"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Region: $REGION" -ForegroundColor Cyan
Write-Host "  S3 Bucket: $BUCKET_NAME" -ForegroundColor Cyan
Write-Host "  CloudFront ID: $CF_DIST_ID" -ForegroundColor Cyan
Write-Host "  API URL: $API_URL" -ForegroundColor Cyan
if (-not $UseHTTPS) {
    Write-Host "  WARNING: ALB does not have HTTPS listener!" -ForegroundColor Yellow
    Write-Host "  Frontend served over HTTPS will have mixed content errors." -ForegroundColor Yellow
    Write-Host "  Run: .\scripts\add-https-to-alb.ps1 to add HTTPS support" -ForegroundColor Yellow
}
Write-Host ""

# Navigate to frontend directory
Push-Location examples/frontend-starter

if (-not (Test-Path "package.json")) {
    Write-Host "ERROR: Frontend directory not found!" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Install/update dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
npm install

# Set environment variables for build
$env:VITE_API_BASE_URL = "$API_URL/api/v1"
if ($COGNITO_USER_POOL_ID) { $env:VITE_COGNITO_USER_POOL_ID = $COGNITO_USER_POOL_ID }
if ($COGNITO_CLIENT_ID) { $env:VITE_COGNITO_CLIENT_ID = $COGNITO_CLIENT_ID }
$env:VITE_COGNITO_REGION = $REGION

Write-Host "Environment variables set:" -ForegroundColor Yellow
Write-Host "  VITE_API_BASE_URL: $env:VITE_API_BASE_URL" -ForegroundColor Cyan
if (-not $UseHTTPS) {
    Write-Host ""
    Write-Host "  ⚠️  WARNING: Using HTTP API URL with HTTPS frontend!" -ForegroundColor Red
    Write-Host "  This will cause mixed content errors in the browser." -ForegroundColor Red
    Write-Host "  See _docs/guides/FIX_MIXED_CONTENT.md for solutions." -ForegroundColor Yellow
}
if ($COGNITO_USER_POOL_ID) {
    Write-Host "  VITE_COGNITO_USER_POOL_ID: $COGNITO_USER_POOL_ID" -ForegroundColor Cyan
    Write-Host "  VITE_COGNITO_CLIENT_ID: $COGNITO_CLIENT_ID" -ForegroundColor Cyan
} else {
    Write-Host "  VITE_COGNITO_USER_POOL_ID: (not set - using demo mode)" -ForegroundColor Yellow
    Write-Host "  VITE_COGNITO_CLIENT_ID: (not set - using demo mode)" -ForegroundColor Yellow
}
Write-Host "  VITE_COGNITO_REGION: $REGION" -ForegroundColor Cyan
Write-Host ""

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Frontend build failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "Frontend build completed successfully!" -ForegroundColor Green
Write-Host ""

# Upload to S3
Write-Host "Uploading frontend to S3..." -ForegroundColor Yellow
aws s3 sync dist/ "s3://$BUCKET_NAME" --delete --region $REGION --profile default1

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: S3 upload failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "Frontend uploaded to S3 successfully!" -ForegroundColor Green
Write-Host ""

Pop-Location

# Configure CloudFront custom error response for SPA routing (404 -> 200 with index.html)
Write-Host "Configuring CloudFront custom error response for SPA routing..." -ForegroundColor Yellow
try {
    # Get current distribution config
    $CF_CONFIG = aws cloudfront get-distribution-config `
        --id $CF_DIST_ID `
        --region $REGION `
        --profile default1 `
        --query 'DistributionConfig' `
        --output json | ConvertFrom-Json
    
    # Check if custom error response already exists
    $has404Error = $false
    if ($CF_CONFIG.CustomErrorResponses -and $CF_CONFIG.CustomErrorResponses.Items) {
        foreach ($errResp in $CF_CONFIG.CustomErrorResponses.Items) {
            if ($errResp.ErrorCode -eq 404) {
                $has404Error = $true
                break
            }
        }
    }
    
    if (-not $has404Error) {
        # Add custom error response for 404
        if (-not $CF_CONFIG.CustomErrorResponses) {
            $CF_CONFIG.CustomErrorResponses = @{
                Quantity = 0
                Items = @()
            }
        }
        
        $CF_CONFIG.CustomErrorResponses.Items += @{
            ErrorCode = 404
            ResponsePagePath = "/index.html"
            ResponseCode = "200"
            ErrorCachingMinTTL = 300
        }
        $CF_CONFIG.CustomErrorResponses.Quantity = $CF_CONFIG.CustomErrorResponses.Items.Count
        
        # Get ETag for update
        $ETAG = aws cloudfront get-distribution-config `
            --id $CF_DIST_ID `
            --region $REGION `
            --profile default1 `
            --query 'ETag' `
            --output text
        
        # Update distribution
        $CF_CONFIG_JSON = $CF_CONFIG | ConvertTo-Json -Depth 10 -Compress
        $CF_CONFIG_JSON | Out-File -FilePath "cloudfront-update.json" -Encoding UTF8 -NoNewline
        
        aws cloudfront update-distribution `
            --id $CF_DIST_ID `
            --distribution-config file://cloudfront-update.json `
            --if-match $ETAG `
            --region $REGION `
            --profile default1 | Out-Null
        
        Remove-Item "cloudfront-update.json" -ErrorAction SilentlyContinue
        
        Write-Host "CloudFront custom error response configured (404 -> 200 with index.html)" -ForegroundColor Green
    } else {
        Write-Host "CloudFront custom error response already configured" -ForegroundColor Cyan
    }
} catch {
    $errMsg = $_.Exception.Message
    Write-Host "WARNING: Could not configure CloudFront custom error response: $errMsg" -ForegroundColor Yellow
    Write-Host "You may need to configure it manually in the AWS Console:" -ForegroundColor Yellow
    Write-Host "  CloudFront -> Distribution -> Error Pages -> Create Custom Error Response" -ForegroundColor Yellow
    Write-Host "  Error Code: 404, Response Page Path: /index.html, HTTP Response Code: 200" -ForegroundColor Yellow
}
Write-Host ""

# Invalidate CloudFront cache
Write-Host "Invalidating CloudFront cache..." -ForegroundColor Yellow
$invalidation = aws cloudfront create-invalidation `
    --distribution-id $CF_DIST_ID `
    --paths "/*" `
    --region $REGION `
    --profile default1 `
    --query 'Invalidation.{Id:Id,Status:Status}' `
    --output json | ConvertFrom-Json

Write-Host "CloudFront invalidation created:" -ForegroundColor Green
Write-Host "  Invalidation ID: $($invalidation.Id)" -ForegroundColor Cyan
Write-Host "  Status: $($invalidation.Status)" -ForegroundColor Cyan
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend URLs:" -ForegroundColor Yellow
Write-Host "  S3 (HTTP): http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com" -ForegroundColor Cyan
Write-Host "  CloudFront (HTTPS): https://$($vars.CF_DOMAIN)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: CloudFront cache invalidation takes 1-2 minutes to complete." -ForegroundColor Yellow
Write-Host "Your changes should be visible shortly!" -ForegroundColor Green

