# Staging Environment Setup Guide

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

See `DEPLOYMENT_CHECKLIST.md` for production deployment steps.
