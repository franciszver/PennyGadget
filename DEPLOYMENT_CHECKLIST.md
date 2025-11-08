# AWS Deployment Quick Checklist

## ✅ Pre-Deployment

- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Docker installed and running
- [ ] Python 3.8+ installed
- [ ] PowerShell 5.1+ available
- [ ] AWS account with admin permissions
- [ ] Cognito User Pool ID: `YOUR_COGNITO_USER_POOL_ID`
- [ ] Cognito Client ID: `YOUR_COGNITO_CLIENT_ID`

## 🚀 Deployment Steps

### Step 1: Initial Setup
```powershell
.\deploy-aws.ps1
```
- [ ] Script completes successfully
- [ ] `aws-deployment-vars.json` created
- [ ] **⏱️ Wait 5-10 minutes for RDS database**

### Step 2: Infrastructure Setup
```powershell
.\deploy-aws-step2.ps1
```
- [ ] ECR repository created
- [ ] Docker image built and pushed
- [ ] IAM roles created
- [ ] ECS cluster created

### Step 3: Backend Deployment
```powershell
.\deploy-aws-step3.ps1
```
- [ ] Task definition registered
- [ ] ALB created
- [ ] Target group created
- [ ] ECS service created
- [ ] **⏱️ Wait 2-3 minutes for service to start**

### Step 4: Database & Demo Users
```powershell
.\deploy-aws-step4.ps1
```
- [ ] Backend health check passes
- [ ] Migrations run successfully
- [ ] Demo users created
- [ ] Demo accounts verified

### Step 5: Frontend Deployment
```powershell
.\deploy-aws-step5.ps1
```
- [ ] S3 bucket created
- [ ] Frontend built successfully
- [ ] Frontend uploaded to S3
- [ ] CloudFront distribution created
- [ ] **⏱️ Wait 10-15 minutes for CloudFront**

## 🔧 Post-Deployment

### Required Actions
- [ ] Add OpenAI API key to ECS task definition
- [ ] Update ECS service to use new task revision
- [ ] Test backend health endpoint
- [ ] Test frontend at CloudFront URL
- [ ] Test demo user logins

### Verification
- [ ] Backend responds at ALB DNS
- [ ] Frontend loads at CloudFront URL
- [ ] Database migrations applied
- [ ] Demo users can log in
- [ ] ECS service shows "RUNNING" status
- [ ] CloudWatch logs accessible

### Optional Enhancements
- [ ] Set up Route 53 custom domain
- [ ] Add ACM SSL certificate
- [ ] Configure HTTPS listener on ALB
- [ ] Set up CloudWatch alarms
- [ ] Configure backup retention
- [ ] Set up monitoring dashboard

## 🐛 Troubleshooting

If something fails:

1. **Check logs**: `aws logs tail /ecs/elevareai-api --follow`
2. **Check ECS service**: `aws ecs describe-services --cluster elevareai-cluster --services elevareai-api`
3. **Check RDS status**: `aws rds describe-db-instances --db-instance-identifier elevareai-db`
4. **Verify security groups**: Check that ECS can access RDS on port 5432
5. **Check task definition**: Ensure all environment variables are set

## 📊 Quick Commands

```powershell
# Load variables
$vars = Get-Content aws-deployment-vars.json | ConvertFrom-Json

# Test backend
Invoke-WebRequest -Uri "http://$($vars.ALB_DNS)/health"

# Check ECS status
aws ecs describe-services --cluster elevareai-cluster --services elevareai-api --query 'services[0].[status,runningCount,desiredCount]' --output table

# View logs
aws logs tail /ecs/elevareai-api --follow

# Check CloudFront
aws cloudfront get-distribution --id $vars.CF_DIST_ID --query 'Distribution.Status' --output text
```

## 📝 Important Values

Save these values securely:

- **Database Password**: Generated in step 1, saved in `aws-deployment-vars.json`
- **RDS Endpoint**: `$vars.DB_ENDPOINT`
- **ALB DNS**: `$vars.ALB_DNS`
- **CloudFront URL**: `https://$vars.CF_DOMAIN`
- **S3 Bucket**: `$vars.BUCKET_NAME`

## 🔐 Security Checklist

- [ ] Database password saved securely
- [ ] OpenAI API key added to ECS (not in code)
- [ ] Security groups properly configured
- [ ] IAM roles have minimal required permissions
- [ ] S3 bucket policy allows public read (for frontend)
- [ ] Consider restricting RDS access further in production
- [ ] Plan to add HTTPS/SSL certificate

## 💰 Cost Monitoring

- [ ] Set up AWS billing alerts
- [ ] Monitor RDS instance usage
- [ ] Monitor ECS Fargate costs
- [ ] Monitor data transfer costs
- [ ] Review CloudFront usage

---

**Estimated Total Time**: 30-45 minutes (including wait times)
**Estimated Monthly Cost**: ~$40-50

