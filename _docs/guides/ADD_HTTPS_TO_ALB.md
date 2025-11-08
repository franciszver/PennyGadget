# Adding HTTPS to ALB - Production Setup

## Problem
Frontend is served over HTTPS (CloudFront) but backend API is HTTP (ALB), causing mixed content errors.

## Solution: Add HTTPS Listener to ALB

### Step 1: Request ACM Certificate

```powershell
# Request certificate (replace with your domain)
aws acm request-certificate `
    --domain-name api.yourdomain.com `
    --validation-method DNS `
    --region us-east-1

# Get certificate ARN from output
$CERT_ARN = "arn:aws:acm:us-east-1:YOUR_ACCOUNT_ID:certificate/xxxxx-xxxxx-xxxxx"
```

**Note**: You need a domain name for ACM certificates. For testing without a domain, use the S3 HTTP URL instead.

### Step 2: Add HTTPS Listener to ALB

```powershell
$vars = Get-Content aws-deployment-vars.json | ConvertFrom-Json
$CERT_ARN = "your-certificate-arn"

aws elbv2 create-listener `
    --load-balancer-arn $vars.ALB_ARN `
    --protocol HTTPS `
    --port 443 `
    --certificates CertificateArn=$CERT_ARN `
    --default-actions Type=forward,TargetGroupArn=$vars.TG_ARN `
    --region us-east-1
```

### Step 3: Rebuild Frontend with HTTPS API URL

```powershell
Push-Location examples/frontend-starter

$vars = Get-Content ../../aws-deployment-vars.json | ConvertFrom-Json
$env:VITE_API_BASE_URL = "https://api.yourdomain.com"  # Or use ALB HTTPS URL
$env:VITE_COGNITO_USER_POOL_ID = "YOUR_COGNITO_USER_POOL_ID"
$env:VITE_COGNITO_CLIENT_ID = "YOUR_COGNITO_CLIENT_ID"
$env:VITE_COGNITO_REGION = "us-east-1"

npm run build
Pop-Location
```

### Step 4: Upload and Invalidate CloudFront

```powershell
$vars = Get-Content aws-deployment-vars.json | ConvertFrom-Json

# Upload to S3
Push-Location examples/frontend-starter
aws s3 sync dist/ "s3://$($vars.BUCKET_NAME)" --delete --region us-east-1
Pop-Location

# Invalidate CloudFront cache
aws cloudfront create-invalidation `
    --distribution-id $vars.CF_DIST_ID `
    --paths "/*" `
    --region us-east-1
```

## Alternative: Use S3 HTTP URL (Temporary)

For testing without a domain, use the S3 HTTP website URL:
- **S3 HTTP URL**: `http://YOUR_BUCKET_NAME.s3-website-us-east-1.amazonaws.com`
- This avoids mixed content since both frontend and backend are HTTP
- Not recommended for production (no HTTPS)

## Current Status

- ✅ Frontend rebuilt with correct API URL
- ✅ CloudFront cache invalidation in progress
- ⚠️  ALB still HTTP only (needs certificate for HTTPS)
- ✅ S3 HTTP URL available as workaround

