#!/bin/bash
# Quick Setup Script
# Sets up the entire development environment quickly

set -e

echo "🚀 AI Study Companion - Quick Setup"
echo "===================================="
echo ""

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.11+"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js not found. Frontend setup will be skipped."
    SKIP_FRONTEND=true
fi

# Create virtual environment
echo "📦 Setting up Python environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt
echo "✅ Python dependencies installed"

# Set up database
echo "🗄️  Setting up database..."
if [ -f ".env" ]; then
    python scripts/setup_db.py || echo "⚠️  Database setup skipped (may need manual configuration)"
else
    echo "⚠️  .env file not found. Creating from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env file created. Please update with your configuration."
    fi
fi

# Set up frontend (if Node.js is available)
if [ -z "$SKIP_FRONTEND" ] && [ -d "examples/frontend-starter" ]; then
    echo "💻 Setting up frontend..."
    cd examples/frontend-starter
    if [ ! -d "node_modules" ]; then
        npm install
        echo "✅ Frontend dependencies installed"
    else
        echo "✅ Frontend dependencies already installed"
    fi
    cd ../..
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your configuration"
echo "2. Start the API: python -m uvicorn src.api.main:app --reload"
echo "3. Start the frontend: cd examples/frontend-starter && npm run dev"
echo ""
echo "API will be available at: http://localhost:8000"
echo "Frontend will be available at: http://localhost:3000"
echo "API docs at: http://localhost:8000/docs"

