#!/bin/bash
# Deploy to Staging Environment
# This script automates the deployment process to staging

set -e

echo "🚀 Starting Staging Deployment..."

# Check if .env.staging exists
if [ ! -f .env.staging ]; then
    echo "❌ .env.staging not found. Run: python scripts/create_staging_env.py"
    exit 1
fi

# Build Docker image
echo "📦 Building Docker image..."
docker build -t pennygadget-api:staging .

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.staging.yml down

# Start containers
echo "▶️  Starting staging environment..."
docker-compose -f docker-compose.staging.yml up -d

# Wait for database to be ready
echo "⏳ Waiting for database..."
sleep 5

# Run migrations
echo "🔄 Running database migrations..."
docker-compose -f docker-compose.staging.yml exec -T api python scripts/setup_db.py || true

# Seed test data (optional)
read -p "Seed test data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌱 Seeding test data..."
    docker-compose -f docker-compose.staging.yml exec -T api python scripts/seed_demo_data.py
fi

# Health check
echo "🏥 Checking API health..."
sleep 3
curl -f http://localhost:8000/health || echo "⚠️  Health check failed - check logs"

echo "✅ Staging deployment complete!"
echo "📊 API available at: http://localhost:8000"
echo "📚 API docs at: http://localhost:8000/docs"

