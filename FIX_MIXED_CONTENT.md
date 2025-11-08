# Fix Mixed Content Error (HTTPS Frontend → HTTP API)

## Problem
The frontend is served over HTTPS via CloudFront, but the API is HTTP-only on the ALB. Browsers block mixed content (HTTPS page making HTTP requests).

## Solution Options

### Option 1: Add HTTPS to ALB (Recommended for Production)

**Requirements:**
- A domain name (e.g., `api.yourdomain.com`)
- ACM certificate for that domain

**Steps:**

1. **Request ACM Certificate:**
   ```powershell
   aws acm request-certificate `
       --domain-name api.yourdomain.com `
       --validation-method DNS `
       --region us-east-1
   ```

2. **Validate the certificate** (add DNS records as instructed by AWS)

3. **Add HTTPS Listener to ALB:**
   ```powershell
   $vars = Get-Content aws-deployment-vars.json | ConvertFrom-Json
   $CERT_ARN = "arn:aws:acm:us-east-1:YOUR_ACCOUNT_ID:certificate/YOUR_CERT_ID"
   
   aws elbv2 create-listener `
       --load-balancer-arn $vars.ALB_ARN `
       --protocol HTTPS `
       --port 443 `
       --certificates CertificateArn=$CERT_ARN `
       --default-actions Type=forward,TargetGroupArn=$vars.TG_ARN `
       --region us-east-1
   ```

4. **Update Frontend Deployment:**
   ```powershell
   .\deploy-frontend.ps1
   ```
   The script will automatically detect HTTPS and use it.

### Option 2: Use Custom Domain with Route 53 (Best Practice)

1. **Set up Route 53 hosted zone** for your domain
2. **Create A record** pointing `api.yourdomain.com` to the ALB
3. **Request ACM certificate** for `api.yourdomain.com`
4. **Add HTTPS listener** using the certificate
5. **Update frontend** to use `https://api.yourdomain.com`

### Option 3: Temporary Workaround (Testing Only)

For testing without a domain, you can temporarily use the S3 HTTP URL:

- **S3 HTTP URL**: `http://YOUR-BUCKET-NAME.s3-website-us-east-1.amazonaws.com`
- This avoids mixed content since both frontend and backend are HTTP
- **Not recommended for production** (no HTTPS, no CloudFront CDN benefits)

### Option 4: Use CloudFront to Proxy API Requests

Configure CloudFront to proxy API requests:
1. Create a CloudFront distribution for the ALB
2. Point API requests to the CloudFront distribution
3. CloudFront handles HTTPS termination

## Current Status

- ✅ Frontend deployment script updated to detect HTTPS
- ⚠️  ALB currently HTTP-only (port 80)
- ⚠️  Need domain + ACM certificate for HTTPS
- ✅ Script created: `scripts/add-https-to-alb.ps1`

## Quick Fix Commands

```powershell
# Check current listeners
$vars = Get-Content aws-deployment-vars.json | ConvertFrom-Json
aws elbv2 describe-listeners --load-balancer-arn $vars.ALB_ARN --query 'Listeners[*].[Port,Protocol]' --output table

# List available certificates
aws acm list-certificates --region us-east-1 --query 'CertificateSummaryList[*].[DomainName,CertificateArn]' --output table

# Add HTTPS listener (after getting certificate)
.\scripts\add-https-to-alb.ps1 -CertificateArn <cert-arn>
```

## Next Steps

1. **For Production**: Set up a custom domain and ACM certificate
2. **For Testing**: Use S3 HTTP URL temporarily
3. **Deploy Frontend**: Run `.\deploy-frontend.ps1` after adding HTTPS

