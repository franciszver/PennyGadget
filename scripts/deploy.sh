#!/bin/bash
# Deployment Script for AI Study Companion API
# Usage: ./scripts/deploy.sh [environment]

set -e  # Exit on error

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "AI Study Companion - Deployment Script"
echo "Environment: $ENVIRONMENT"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    exit 1
fi

# Load environment variables
if [ -f "$PROJECT_DIR/.env.$ENVIRONMENT" ]; then
    echo -e "${GREEN}Loading environment variables from .env.$ENVIRONMENT${NC}"
    export $(cat "$PROJECT_DIR/.env.$ENVIRONMENT" | grep -v '^#' | xargs)
elif [ -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}Warning: Using .env file (consider using .env.$ENVIRONMENT)${NC}"
    export $(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}Warning: No .env file found. Using defaults.${NC}"
fi

cd "$PROJECT_DIR"

# Build Docker image
echo ""
echo -e "${GREEN}Building Docker image...${NC}"
docker-compose build --no-cache api

# Run database migrations (if using Alembic)
if [ -f "$PROJECT_DIR/alembic.ini" ]; then
    echo ""
    echo -e "${GREEN}Running database migrations...${NC}"
    docker-compose run --rm api alembic upgrade head || echo -e "${YELLOW}Warning: Migrations failed or not configured${NC}"
fi

# Start services
echo ""
echo -e "${GREEN}Starting services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo ""
echo -e "${GREEN}Waiting for services to be healthy...${NC}"
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker-compose ps | grep -q "healthy"; then
        echo -e "${GREEN}Services are healthy!${NC}"
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    echo -n "."
done

if [ $elapsed -ge $timeout ]; then
    echo -e "${RED}Timeout waiting for services to be healthy${NC}"
    docker-compose logs
    exit 1
fi

# Health check
echo ""
echo -e "${GREEN}Performing health check...${NC}"
sleep 5
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    docker-compose logs api
    exit 1
fi

# Display service status
echo ""
echo -e "${GREEN}Service Status:${NC}"
docker-compose ps

echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "API URL: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Health: http://localhost:8000/health"
echo ""
echo "To view logs: docker-compose logs -f api"
echo "To stop: docker-compose down"
echo ""

