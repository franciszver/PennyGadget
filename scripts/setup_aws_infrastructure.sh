#!/bin/bash
# AWS Infrastructure Setup Script
# Run with: bash scripts/setup_aws_infrastructure.sh --profile your-profile-name

set -e  # Exit on error

# Parse command line arguments
PROFILE=""
REGION="us-east-1"
ENVIRONMENT="development"

while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--profile PROFILE] [--region REGION] [--environment ENV]"
      exit 1
      ;;
  esac
done

# Set AWS profile if provided
if [ -n "$PROFILE" ]; then
  export AWS_PROFILE="$PROFILE"
  echo "Using AWS profile: $PROFILE"
fi

echo "=========================================="
echo "AI Study Companion - AWS Infrastructure Setup"
echo "=========================================="
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"
echo ""

# Generate random suffix for resource names
RANDOM_SUFFIX=$(openssl rand -hex 4)
STACK_NAME="pennygadget-${ENVIRONMENT}-${RANDOM_SUFFIX}"

echo "Stack name: $STACK_NAME"
echo ""

# ============================================================================
# Step 1: Create RDS PostgreSQL Database
# ============================================================================
echo "Step 1: Creating RDS PostgreSQL database..."

DB_INSTANCE_ID="pennygadget-db-${ENVIRONMENT}"
DB_NAME="pennygadget"
DB_USER="admin"
DB_PASSWORD=$(openssl rand -base64 32)

# Check if DB instance already exists
if aws rds describe-db-instances --db-instance-identifier "$DB_INSTANCE_ID" --region "$REGION" 2>/dev/null | grep -q "$DB_INSTANCE_ID"; then
  echo "  ⚠️  RDS instance already exists: $DB_INSTANCE_ID"
  echo "  Getting existing endpoint..."
  DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier "$DB_INSTANCE_ID" \
    --region "$REGION" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)
else
  echo "  Creating RDS PostgreSQL instance..."
  aws rds create-db-instance \
    --db-instance-identifier "$DB_INSTANCE_ID" \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.4 \
    --master-username "$DB_USER" \
    --master-user-password "$DB_PASSWORD" \
    --allocated-storage 20 \
    --storage-type gp2 \
    --db-name "$DB_NAME" \
    --backup-retention-period 7 \
    --region "$REGION" \
    --no-multi-az \
    --publicly-accessible \
    --storage-encrypted \
    > /dev/null
  
  echo "  ⏳ Waiting for database to be available (this may take 5-10 minutes)..."
  aws rds wait db-instance-available \
    --db-instance-identifier "$DB_INSTANCE_ID" \
    --region "$REGION"
  
  DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier "$DB_INSTANCE_ID" \
    --region "$REGION" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)
fi

echo "  ✅ Database created: $DB_ENDPOINT"
echo ""

# ============================================================================
# Step 2: Create Cognito User Pool
# ============================================================================
echo "Step 2: Creating Cognito User Pool..."

USER_POOL_NAME="pennygadget-users-${ENVIRONMENT}"

# Check if user pool already exists
EXISTING_POOL=$(aws cognito-idp list-user-pools \
  --max-results 60 \
  --region "$REGION" \
  --query "UserPools[?Name=='${USER_POOL_NAME}'].Id" \
  --output text)

if [ -n "$EXISTING_POOL" ]; then
  echo "  ⚠️  User pool already exists: $EXISTING_POOL"
  USER_POOL_ID="$EXISTING_POOL"
else
  echo "  Creating Cognito User Pool..."
  USER_POOL_ID=$(aws cognito-idp create-user-pool \
    --pool-name "$USER_POOL_NAME" \
    --policies "PasswordPolicy={MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=true}" \
    --auto-verified-attributes email \
    --region "$REGION" \
    --query 'UserPool.Id' \
    --output text)
  
  echo "  ✅ User Pool created: $USER_POOL_ID"
fi

# Create User Pool Client
CLIENT_NAME="pennygadget-client-${ENVIRONMENT}"

EXISTING_CLIENT=$(aws cognito-idp list-user-pool-clients \
  --user-pool-id "$USER_POOL_ID" \
  --region "$REGION" \
  --query "UserPoolClients[?ClientName=='${CLIENT_NAME}'].ClientId" \
  --output text)

if [ -n "$EXISTING_CLIENT" ]; then
  echo "  ⚠️  User pool client already exists: $EXISTING_CLIENT"
  CLIENT_ID="$EXISTING_CLIENT"
else
  echo "  Creating User Pool Client..."
  CLIENT_ID=$(aws cognito-idp create-user-pool-client \
    --user-pool-id "$USER_POOL_ID" \
    --client-name "$CLIENT_NAME" \
    --generate-secret \
    --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
    --region "$REGION" \
    --query 'UserPoolClient.ClientId' \
    --output text)
  
  echo "  ✅ User Pool Client created: $CLIENT_ID"
fi

# Create User Groups (roles)
echo "  Creating user groups (roles)..."
for ROLE in student tutor parent admin; do
  GROUP_NAME="${ROLE}s"
  if ! aws cognito-idp get-group \
    --user-pool-id "$USER_POOL_ID" \
    --group-name "$GROUP_NAME" \
    --region "$REGION" 2>/dev/null; then
    aws cognito-idp create-group \
      --user-pool-id "$USER_POOL_ID" \
      --group-name "$GROUP_NAME" \
      --description "Users with ${ROLE} role" \
      --region "$REGION" > /dev/null
    echo "    ✅ Created group: $GROUP_NAME"
  else
    echo "    ⚠️  Group already exists: $GROUP_NAME"
  fi
done

echo ""

# ============================================================================
# Step 3: Configure SES (Simple Email Service)
# ============================================================================
echo "Step 3: Configuring SES for email..."

# Get account sending quota
SES_QUOTA=$(aws ses get-account-sending-enabled \
  --region "$REGION" \
  --query 'Enabled' \
  --output text 2>/dev/null || echo "false")

if [ "$SES_QUOTA" = "false" ]; then
  echo "  ⚠️  SES is in sandbox mode. You'll need to:"
  echo "     1. Verify your email address: aws ses verify-email-identity --email-address your@email.com --region $REGION"
  echo "     2. Request production access: https://console.aws.amazon.com/ses/home?region=$REGION#/account/settings"
else
  echo "  ✅ SES is enabled"
fi

echo ""

# ============================================================================
# Step 4: Create S3 Bucket for Transcripts (Optional)
# ============================================================================
echo "Step 4: Creating S3 bucket for transcripts..."

BUCKET_NAME="pennygadget-transcripts-${ENVIRONMENT}-${RANDOM_SUFFIX}"

if aws s3 ls "s3://${BUCKET_NAME}" 2>/dev/null; then
  echo "  ⚠️  S3 bucket already exists: $BUCKET_NAME"
else
  if [ "$REGION" = "us-east-1" ]; then
    aws s3 mb "s3://${BUCKET_NAME}" --region "$REGION" > /dev/null
  else
    aws s3 mb "s3://${BUCKET_NAME}" --region "$REGION" > /dev/null
  fi
  
  # Enable versioning
  aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled \
    --region "$REGION" > /dev/null
  
  echo "  ✅ S3 bucket created: $BUCKET_NAME"
fi

echo ""

# ============================================================================
# Step 5: Save Configuration
# ============================================================================
echo "Step 5: Saving configuration..."

CONFIG_FILE=".aws-config-${ENVIRONMENT}.env"

cat > "$CONFIG_FILE" << EOF
# AWS Infrastructure Configuration
# Generated: $(date)
# Environment: $ENVIRONMENT
# Region: $REGION

# Database (RDS PostgreSQL)
DB_HOST=$DB_ENDPOINT
DB_PORT=5432
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD

# Cognito
COGNITO_USER_POOL_ID=$USER_POOL_ID
COGNITO_CLIENT_ID=$CLIENT_ID
COGNITO_REGION=$REGION

# SES
SES_REGION=$REGION
SES_FROM_EMAIL=noreply@yourdomain.com

# S3
S3_BUCKET_NAME=$BUCKET_NAME
S3_REGION=$REGION

# AWS Region
AWS_REGION=$REGION
EOF

echo "  ✅ Configuration saved to: $CONFIG_FILE"
echo "  ⚠️  IMPORTANT: Add these values to your .env file!"
echo "  ⚠️  IMPORTANT: Keep DB_PASSWORD secure!"
echo ""

# ============================================================================
# Summary
# ============================================================================
echo "=========================================="
echo "✅ Infrastructure Setup Complete!"
echo "=========================================="
echo ""
echo "Resources created:"
echo "  📊 RDS Database: $DB_ENDPOINT"
echo "  🔐 Cognito User Pool: $USER_POOL_ID"
echo "  📧 SES: Configured (may need verification)"
echo "  📦 S3 Bucket: $BUCKET_NAME"
echo ""
echo "Next steps:"
echo "  1. Copy values from $CONFIG_FILE to your .env file"
echo "  2. Run database migrations: python scripts/setup_db.py"
echo "  3. Verify SES email: aws ses verify-email-identity --email-address your@email.com --region $REGION"
echo "  4. Test connection to database"
echo ""
echo "⚠️  Security Notes:"
echo "  - Database password is in $CONFIG_FILE (keep secure!)"
echo "  - RDS instance is publicly accessible (restrict in production)"
echo "  - Add security groups to restrict database access"
echo ""

