# Troubleshooting Guide

## Common Issues and Solutions

### PostgreSQL Version Not Available

**Error:** `Cannot find version 15.4 for postgres`

**Solution:** The script now automatically detects available PostgreSQL versions. If you still see this error:

1. **Check available versions manually:**
   ```powershell
   aws rds describe-db-engine-versions --engine postgres --region us-east-1 --query 'DBEngineVersions[].EngineVersion' --output table
   ```

2. **Manually create database with available version:**
   ```powershell
   aws rds create-db-instance `
     --db-instance-identifier pennygadget-db-development `
     --db-instance-class db.t3.micro `
     --engine postgres `
     --engine-version 14.9 `
     --master-username admin `
     --master-user-password YourPassword123! `
     --allocated-storage 20 `
     --storage-type gp2 `
     --db-name pennygadget `
     --backup-retention-period 7 `
     --region us-east-1 `
     --publicly-accessible `
     --storage-encrypted
   ```

### Database Creation Failed

**Error:** `DBInstanceNotFound` or `Waiter DBInstanceAvailable failed`

**Solutions:**
1. Check AWS Console → RDS → Databases to see if instance exists
2. Check CloudWatch logs for errors
3. Verify you have RDS permissions
4. Check if you've hit RDS instance quota limits

### Profile Not Found

**Error:** `The config profile (profile-name) could not be found`

**Solution:**
```powershell
# List available profiles
aws configure list-profiles

# Configure a new profile
aws configure --profile your-profile-name

# Test the profile
aws sts get-caller-identity --profile your-profile-name
```

### Permission Denied Errors

**Error:** `AccessDenied` or `UnauthorizedOperation`

**Solution:** Your AWS user/role needs these permissions:
- `rds:CreateDBInstance`
- `rds:DescribeDBInstances`
- `cognito-idp:*`
- `ses:*`
- `s3:CreateBucket`
- `s3:PutBucketVersioning`

Create an IAM policy or use an admin role for development.

### Database Connection Issues After Creation

**Symptoms:** Can't connect to database after setup

**Solutions:**
1. **Wait 5-10 minutes** - RDS takes time to become available
2. **Check security groups:**
   ```powershell
   # Get security group ID
   aws rds describe-db-instances --db-instance-identifier pennygadget-db-development --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' --output text
   
   # Add your IP to security group (replace SG-ID and YOUR-IP)
   aws ec2 authorize-security-group-ingress --group-id sg-xxxxx --protocol tcp --port 5432 --cidr YOUR-IP/32
   ```

3. **Verify credentials in `.env` file**

### Cognito User Pool Creation Fails

**Error:** `InvalidParameterException` or similar

**Solutions:**
1. Check if pool name already exists (must be unique globally)
2. Verify region supports Cognito
3. Check IAM permissions for Cognito

### S3 Bucket Creation Fails

**Error:** `BucketAlreadyExists` or `InvalidBucketName`

**Solutions:**
1. S3 bucket names must be globally unique
2. The script generates a random suffix - if it still fails, bucket name might be taken
3. Try a different environment name: `-Environment dev2`

### Script Hangs on "Waiting for database"

**Solution:**
1. Database creation can take 10-15 minutes
2. Check AWS Console to see actual status
3. If it's been > 15 minutes, check for errors in CloudWatch
4. You can cancel (Ctrl+C) and check status manually:
   ```powershell
   aws rds describe-db-instances --db-instance-identifier pennygadget-db-development --query 'DBInstances[0].DBInstanceStatus'
   ```

## Manual Setup Steps

If the script fails, you can set up manually:

### 1. Create RDS Database
```powershell
aws rds create-db-instance `
  --db-instance-identifier pennygadget-db-development `
  --db-instance-class db.t3.micro `
  --engine postgres `
  --engine-version 14.9 `
  --master-username admin `
  --master-user-password YourSecurePassword123! `
  --allocated-storage 20 `
  --db-name pennygadget `
  --backup-retention-period 7 `
  --publicly-accessible `
  --storage-encrypted
```

### 2. Create Cognito User Pool
```powershell
aws cognito-idp create-user-pool `
  --pool-name pennygadget-users-development `
  --auto-verified-attributes email
```

### 3. Create S3 Bucket
```powershell
aws s3 mb s3://pennygadget-transcripts-development-$(Get-Random)
```

Then manually create `.env` file with the values.

## Getting Help

1. Check AWS CloudWatch logs
2. Check AWS Console for resource status
3. Verify all prerequisites are met
4. Review error messages carefully - they often indicate the specific issue

## Cleanup (If Needed)

To delete all resources created:

```powershell
# Delete RDS (takes time)
aws rds delete-db-instance --db-instance-identifier pennygadget-db-development --skip-final-snapshot

# Delete Cognito User Pool
aws cognito-idp delete-user-pool --user-pool-id <pool-id>

# Delete S3 Bucket
aws s3 rb s3://pennygadget-transcripts-development-xxxxx --force
```

