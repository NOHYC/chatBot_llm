#!/bin/bash

# Startup script for Soccer Chat API Server

echo "Starting Soccer Chat API Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found."
    echo "Using default configuration from config.py"
fi

# Start the server
echo "Starting server on http://localhost:8001"
echo "API documentation available at http://localhost:8001/docs"
uvicorn main:app --reload --host 0.0.0.0 --port 8001
