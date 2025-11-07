#!/bin/bash
# Quick Demo Setup Script
# Sets up environment for demo

echo "=========================================="
echo "AI Study Companion - Demo Quick Start"
echo "=========================================="
echo ""

# Check if server is running
echo "[1/4] Checking server status..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "[OK] Server is running"
else
    echo "[WARNING] Server not running. Start with: python run_server.py"
fi

# Check database connection
echo ""
echo "[2/4] Checking database connection..."
python -c "
from src.config.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        result.fetchone()
    print('[OK] Database connected')
except Exception as e:
    print(f'[ERROR] Database connection failed: {e}')
"

# Check demo data
echo ""
echo "[3/4] Checking demo data..."
if [ -f "scripts/demo_data.json" ]; then
    echo "[OK] Demo data file exists"
else
    echo "[INFO] Run 'python scripts/seed_demo_data.py' to generate demo data"
fi

# Show available endpoints
echo ""
echo "[4/4] Available Demo Endpoints:"
echo "  - Health: GET http://localhost:8000/health"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Summaries: POST http://localhost:8000/api/v1/summaries"
echo "  - Practice: POST http://localhost:8000/api/v1/practice/assign"
echo "  - Q&A: POST http://localhost:8000/api/v1/qa/query"
echo "  - Progress: GET http://localhost:8000/api/v1/progress/{student_id}"
echo ""

echo "=========================================="
echo "Demo Setup Complete!"
echo "=========================================="
echo ""
echo "See DEMO_GUIDE.md for demo scenarios"
echo ""

