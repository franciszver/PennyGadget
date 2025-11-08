# AWS Deployment - Step 5: Deploy Frontend
# Load variables
$vars = Get-Content "aws-deployment-vars.json" | ConvertFrom-Json

$REGION = $vars.REGION
$PROJECT_NAME = $vars.PROJECT_NAME
$ALB_DNS = $vars.ALB_DNS

# Step 20: Create S3 Bucket for Frontend
Write-Host "Step 20: Creating S3 bucket..." -ForegroundColor Cyan
$BUCKET_NAME = "$PROJECT_NAME-frontend-$(Get-Random -Minimum 1000 -Maximum 9999)"
Write-Host "Creating S3 bucket: $BUCKET_NAME" -ForegroundColor Yellow

aws s3 mb "s3://$BUCKET_NAME" --region $REGION

# Enable static website hosting
aws s3 website "s3://$BUCKET_NAME/" --index-document index.html --error-document index.html

# Create bucket policy for public read access
$BUCKET_POLICY = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Sid = "PublicReadGetObject"
            Effect = "Allow"
            Principal = "*"
            Action = "s3:GetObject"
            Resource = "arn:aws:s3:::$BUCKET_NAME/*"
        }
    )
} | ConvertTo-Json -Compress

aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy $BUCKET_POLICY
Write-Host "S3 bucket created: $BUCKET_NAME" -ForegroundColor Green

# Step 21: Build and Upload Frontend
Write-Host "`nStep 21: Building and uploading frontend..." -ForegroundColor Cyan

# Navigate to frontend directory
Push-Location examples/frontend-starter

# Install dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
npm install

# Get Cognito IDs from vars file or environment variables
$COGNITO_USER_POOL_ID = if ($vars.COGNITO_USER_POOL_ID) { $vars.COGNITO_USER_POOL_ID } else { $env:COGNITO_USER_POOL_ID }
$COGNITO_CLIENT_ID = if ($vars.COGNITO_CLIENT_ID) { $vars.COGNITO_CLIENT_ID } else { $env:COGNITO_CLIENT_ID }

if (-not $COGNITO_USER_POOL_ID -or -not $COGNITO_CLIENT_ID) {
    Write-Host "ERROR: Cognito credentials not found!" -ForegroundColor Red
    Write-Host "Please set COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID environment variables" -ForegroundColor Red
    Write-Host "Or add them to aws-deployment-vars.json" -ForegroundColor Red
    exit 1
}

# Set API URL environment variable for build
$env:VITE_API_BASE_URL = "http://$ALB_DNS"
$env:VITE_COGNITO_USER_POOL_ID = $COGNITO_USER_POOL_ID
$env:VITE_COGNITO_CLIENT_ID = $COGNITO_CLIENT_ID
$env:VITE_COGNITO_REGION = $REGION

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Yellow
npm run build

# Upload to S3
Write-Host "Uploading frontend to S3..." -ForegroundColor Yellow
aws s3 sync dist/ "s3://$BUCKET_NAME" --delete --region $REGION

Write-Host "Frontend uploaded to S3!" -ForegroundColor Green

# Get S3 website URL
$S3_WEBSITE_URL = "http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
Write-Host "Frontend S3 URL: $S3_WEBSITE_URL" -ForegroundColor Green

Pop-Location

# Step 22: Create CloudFront Distribution
Write-Host "`nStep 22: Creating CloudFront distribution..." -ForegroundColor Cyan
$CF_ORIGIN_ID = "$PROJECT_NAME-frontend-origin"
$CF_DIST_CONFIG = @{
    CallerReference = "$(Get-Date -Format 'yyyyMMddHHmmss')"
    Comment = "ElevareAI Frontend Distribution"
    DefaultCacheBehavior = @{
        TargetOriginId = $CF_ORIGIN_ID
        ViewerProtocolPolicy = "redirect-to-https"
        AllowedMethods = @("GET", "HEAD", "OPTIONS")
        CachedMethods = @("GET", "HEAD")
        ForwardedValues = @{
            QueryString = $false
            Cookies = @{
                Forward = "none"
            }
        }
        MinTTL = 0
        DefaultTTL = 86400
        MaxTTL = 31536000
    }
    Origins = @(
        @{
            Id = $CF_ORIGIN_ID
            DomainName = "$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
            CustomOriginConfig = @{
                HTTPPort = 80
                HTTPSPort = 443
                OriginProtocolPolicy = "http-only"
            }
        }
    )
    Enabled = $true
    PriceClass = "PriceClass_100"
} | ConvertTo-Json -Depth 10

$CF_DIST_CONFIG | Out-File -FilePath "cloudfront-config.json" -Encoding UTF8

$CF_DIST = aws cloudfront create-distribution --distribution-config file://cloudfront-config.json --query 'Distribution.{Id:Id,DomainName:DomainName,Status:Status}' --output json | ConvertFrom-Json

Write-Host "CloudFront Distribution ID: $($CF_DIST.Id)" -ForegroundColor Green
Write-Host "CloudFront Domain: $($CF_DIST.DomainName)" -ForegroundColor Green
Write-Host "Status: $($CF_DIST.Status)" -ForegroundColor Yellow
Write-Host "Note: CloudFront takes 10-15 minutes to deploy" -ForegroundColor Cyan

# Update variables
$vars | Add-Member -NotePropertyName BUCKET_NAME -NotePropertyValue $BUCKET_NAME -Force
$vars | Add-Member -NotePropertyName S3_WEBSITE_URL -NotePropertyValue $S3_WEBSITE_URL -Force
$vars | Add-Member -NotePropertyName CF_DIST_ID -NotePropertyValue $CF_DIST.Id -Force
$vars | Add-Member -NotePropertyName CF_DOMAIN -NotePropertyValue $CF_DIST.DomainName -Force
$vars | ConvertTo-Json | Out-File -FilePath "aws-deployment-vars.json" -Encoding UTF8

# Step 23: Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "AWS Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Backend API:" -ForegroundColor Yellow
Write-Host "  URL: http://$ALB_DNS" -ForegroundColor Green
Write-Host "  Health: http://$ALB_DNS/health" -ForegroundColor Green

Write-Host "`nFrontend:" -ForegroundColor Yellow
Write-Host "  S3 URL: $S3_WEBSITE_URL" -ForegroundColor Green
Write-Host "  CloudFront: https://$($CF_DIST.DomainName)" -ForegroundColor Green

Write-Host "`nDatabase:" -ForegroundColor Yellow
Write-Host "  Endpoint: $($vars.DB_ENDPOINT)" -ForegroundColor Green

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Add OPENAI_API_KEY to ECS task definition" -ForegroundColor Cyan
Write-Host "  2. Wait for CloudFront to deploy (10-15 minutes)" -ForegroundColor Cyan
Write-Host "  3. Test frontend at: https://$($CF_DIST.DomainName)" -ForegroundColor Cyan
Write-Host "  4. Test backend at: http://$ALB_DNS/health" -ForegroundColor Cyan
Write-Host "  5. Test demo users login" -ForegroundColor Cyan

