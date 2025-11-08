#!/usr/bin/env python3
"""
Staging Environment Setup Script
Creates a staging environment configuration for testing before production
"""

import os
import json
from pathlib import Path


def create_staging_env_file():
    """Create .env.staging file with staging configuration"""
    staging_env = {
        "ENVIRONMENT": "staging",
        "LOG_LEVEL": "INFO",
        "API_VERSION": "v1",
        
        # Database (use staging database)
        "DATABASE_URL": "postgresql://user:password@staging-db:5432/pennygadget_staging",
        "DATABASE_POOL_SIZE": "10",
        
        # AWS (staging credentials)
        "AWS_REGION": "us-east-1",
        "COGNITO_USER_POOL_ID": "us-east-1_STAGING_POOL_ID",
        "COGNITO_CLIENT_ID": "staging_client_id",
        
        # OpenAI (staging key)
        "OPENAI_API_KEY": "sk-staging-key-here",
        
        # Email (staging SES)
        "AWS_SES_REGION": "us-east-1",
        "AWS_SES_FROM_EMAIL": "staging@yourdomain.com",
        
        # Frontend
        "FRONTEND_BASE_URL": "https://staging.yourdomain.com",
        
        # Feature Flags
        "ENABLE_GAMIFICATION": "true",
        "ENABLE_ANALYTICS": "true",
        "ENABLE_INTEGRATIONS": "true",
        
        # Monitoring
        "ENABLE_METRICS": "true",
        "ENABLE_LOGGING": "true",
    }
    
    env_content = "\n".join([f"{key}={value}" for key, value in staging_env.items()])
    
    env_file = Path(".env.staging")
    env_file.write_text(env_content)
    
    print(f"[OK] Created {env_file}")
    print("\n[INFO] Next steps:")
    print("1. Update DATABASE_URL with your staging database")
    print("2. Update AWS credentials")
    print("3. Update OpenAI API key")
    print("4. Update email configuration")
    print("5. Review and adjust feature flags")


def create_docker_compose_staging():
    """Create docker-compose.staging.yml for staging environment"""
    docker_compose = {
        "services": {
            "api": {
                "build": ".",
                "ports": ["8000:8000"],
                "environment": {
                    "ENVIRONMENT": "staging",
                    "DATABASE_URL": "postgresql://pennygadget:password@db:5432/pennygadget_staging"
                },
                "env_file": [".env.staging"],
                "depends_on": ["db"],
                "volumes": ["./src:/app/src"]
            },
            "db": {
                "image": "postgres:15-alpine",
                "environment": {
                    "POSTGRES_USER": "pennygadget",
                    "POSTGRES_PASSWORD": "password",
                    "POSTGRES_DB": "pennygadget_staging"
                },
                "volumes": ["postgres_staging_data:/var/lib/postgresql/data"],
                "ports": ["5433:5432"]
            }
        },
        "volumes": {
            "postgres_staging_data": {}
        }
    }
    
    compose_file = Path("docker-compose.staging.yml")
    with open(compose_file, "w") as f:
        import yaml
        yaml.dump(docker_compose, f, default_flow_style=False)
    
    print(f"[OK] Created {compose_file}")


def create_staging_readme():
    """Create STAGING_SETUP.md guide"""
    readme_content = """# Staging Environment Setup Guide

## Overview
This guide helps you set up a staging environment for testing before production deployment.

## Prerequisites
- Docker and Docker Compose installed
- AWS account (for staging resources)
- Database access

## Quick Start

### 1. Create Staging Environment File
```bash
python scripts/create_staging_env.py
```

### 2. Update Configuration
Edit `.env.staging` with your staging credentials:
- Database URL
- AWS credentials
- API keys
- Service endpoints

### 3. Start Staging Environment
```bash
docker-compose -f docker-compose.staging.yml up -d
```

### 4. Run Migrations
```bash
docker-compose -f docker-compose.staging.yml exec api python scripts/setup_db.py
```

### 5. Seed Test Data
```bash
docker-compose -f docker-compose.staging.yml exec api python scripts/seed_demo_data.py
```

## Staging vs Production

### Staging Environment
- Separate database
- Staging AWS resources
- Test API keys
- Development logging
- Feature flags enabled

### Production Environment
- Production database
- Production AWS resources
- Production API keys
- Production logging
- Feature flags as needed

## Testing Checklist

- [ ] API endpoints working
- [ ] Database connections
- [ ] External service integrations
- [ ] Authentication flow
- [ ] Email notifications
- [ ] Push notifications
- [ ] Webhook delivery
- [ ] Performance acceptable
- [ ] Error handling
- [ ] Monitoring working

## Troubleshooting

### Database Connection Issues
- Check DATABASE_URL in .env.staging
- Verify database container is running
- Check network connectivity

### AWS Service Issues
- Verify AWS credentials
- Check IAM permissions
- Verify service endpoints

### API Issues
- Check logs: `docker-compose -f docker-compose.staging.yml logs api`
- Verify environment variables
- Check service health: `curl http://localhost:8000/health`

## Next Steps

1. Complete staging setup
2. Run integration tests
3. Perform user acceptance testing
4. Fix any issues
5. Proceed to production deployment

See `_docs/guides/AWS_DEPLOYMENT_CHECKLIST.md` for AWS deployment steps.
"""
    
    readme_file = Path("STAGING_SETUP.md")
    readme_file.write_text(readme_content)
    
    print(f"[OK] Created {readme_file}")


def main():
    """Main setup function"""
    print("[SETUP] Creating staging environment configuration...\n")
    
    try:
        create_staging_env_file()
        create_staging_readme()
        
        print("\n[OK] Staging environment setup complete!")
        print("\n[INFO] Note: docker-compose.staging.yml requires PyYAML")
        print("      Install with: pip install pyyaml")
        
    except Exception as e:
        print(f"[ERROR] Error creating staging setup: {str(e)}")
        raise


if __name__ == "__main__":
    main()

