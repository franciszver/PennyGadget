#!/bin/bash
# Start AI Study Companion API Server
# Usage: ./START_SERVER.sh

echo "Starting AI Study Companion API Server..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3.11+"
    exit 1
fi

echo "Python: $(python3 --version)"
echo ""

# Check if uvicorn is available
if ! python3 -m uvicorn --version &> /dev/null; then
    echo "Installing uvicorn..."
    python3 -m pip install uvicorn[standard] fastapi
fi

echo ""
echo "Starting server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

