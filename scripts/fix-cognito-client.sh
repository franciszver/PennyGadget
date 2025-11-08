#!/bin/bash
# Fix Cognito Client - Enable USER_SRP_AUTH
# This script updates an existing Cognito User Pool Client to enable USER_SRP_AUTH
# which is required by amazon-cognito-identity-js for authentication

set -e

USER_POOL_ID=""
CLIENT_ID=""
REGION="us-east-1"
PROFILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --user-pool-id)
            USER_POOL_ID="$2"
            shift 2
            ;;
        --client-id)
            CLIENT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "Fix Cognito Client - Enable USER_SRP_AUTH"
echo "========================================"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI is not installed or not in PATH"
    exit 1
fi

# Try to get values from aws-deployment-vars.json if not provided
if [ -z "$USER_POOL_ID" ] || [ -z "$CLIENT_ID" ]; then
    if [ -f "aws-deployment-vars.json" ]; then
        echo "Reading configuration from aws-deployment-vars.json..."
        if command -v jq &> /dev/null; then
            if [ -z "$USER_POOL_ID" ]; then
                USER_POOL_ID=$(jq -r '.COGNITO_USER_POOL_ID // empty' aws-deployment-vars.json)
            fi
            if [ -z "$CLIENT_ID" ]; then
                CLIENT_ID=$(jq -r '.COGNITO_CLIENT_ID // empty' aws-deployment-vars.json)
            fi
            if [ -z "$REGION" ]; then
                REGION=$(jq -r '.REGION // "us-east-1"' aws-deployment-vars.json)
            fi
        fi
    fi
fi

# Validate required parameters
if [ -z "$USER_POOL_ID" ]; then
    echo "ERROR: User Pool ID is required"
    echo "Usage: ./fix-cognito-client.sh --user-pool-id <pool-id> --client-id <client-id> [--region <region>] [--profile <profile>]"
    exit 1
fi

if [ -z "$CLIENT_ID" ]; then
    echo "ERROR: Client ID is required"
    echo "Usage: ./fix-cognito-client.sh --user-pool-id <pool-id> --client-id <client-id> [--region <region>] [--profile <profile>]"
    exit 1
fi

echo "Configuration:"
echo "  User Pool ID: $USER_POOL_ID"
echo "  Client ID: $CLIENT_ID"
echo "  Region: $REGION"
if [ -n "$PROFILE" ]; then
    echo "  Profile: $PROFILE"
fi
echo ""

# Build AWS CLI command
PROFILE_ARG=""
if [ -n "$PROFILE" ]; then
    PROFILE_ARG="--profile $PROFILE"
fi

# First, get the current client configuration
echo "Fetching current client configuration..."
if aws cognito-idp describe-user-pool-client \
    --user-pool-id "$USER_POOL_ID" \
    --client-id "$CLIENT_ID" \
    --region "$REGION" \
    $PROFILE_ARG \
    --output json > /dev/null 2>&1; then
    echo "  [OK] Current client configuration retrieved"
else
    echo "  [ERROR] Failed to retrieve client configuration"
    exit 1
fi

# Update the client with USER_SRP_AUTH enabled
echo ""
echo "Updating client to enable USER_SRP_AUTH..."

if aws cognito-idp update-user-pool-client \
    --user-pool-id "$USER_POOL_ID" \
    --client-id "$CLIENT_ID" \
    --explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
    --region "$REGION" \
    $PROFILE_ARG \
    --output json > /dev/null; then
    echo "  [OK] Client updated successfully!"
    echo ""
    echo "Updated authentication flows:"
    echo "  - ALLOW_USER_SRP_AUTH"
    echo "  - ALLOW_USER_PASSWORD_AUTH"
    echo "  - ALLOW_REFRESH_TOKEN_AUTH"
    echo ""
    echo "========================================"
    echo "Fix Complete!"
    echo "========================================"
    echo ""
    echo "The Cognito client now supports USER_SRP_AUTH."
    echo "Users should now be able to log in successfully."
else
    echo "  [ERROR] Failed to update client"
    echo ""
    echo "You may need to manually update the client in the AWS Console:"
    echo "  1. Go to AWS Cognito Console"
    echo "  2. Select your User Pool"
    echo "  3. Go to App integration > App clients"
    echo "  4. Edit your client"
    echo "  5. Enable 'ALLOW_USER_SRP_AUTH' in Authentication flows"
    exit 1
fi

