#!/bin/bash

# Real-time Trading Signals Dashboard Startup Script

echo "🚀 Starting Real-time Trading Signals Dashboard..."

# Create logs directory
mkdir -p logs

# Check if MongoDB is running
echo "🔍 Checking MongoDB connection..."
if ! timeout 5 bash -c "</dev/tcp/localhost/27017" 2>/dev/null; then
    echo "❌ MongoDB is not running on port 27017"
    echo "Please start MongoDB with: docker run -d --name mongo-container -p 27017:27017 mongo:latest"
    exit 1
fi
echo "✅ MongoDB is running"

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if ! timeout 5 bash -c "</dev/tcp/localhost/6379" 2>/dev/null; then
    echo "❌ Redis is not running on port 6379"
    echo "Please start Redis with: docker run -d --name redis-container -p 6379:6379 redis:7-alpine"
    exit 1
fi
echo "✅ Redis is running"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️ .env file not found, creating from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📝 Please edit .env file with your credentials:"
        echo "   - TRADING_FIIN_USERNAME"
        echo "   - TRADING_FIIN_PASSWORD"
        echo "   - TRADING_TELEGRAM_BOT_TOKEN (optional)"
        echo "   - TRADING_TELEGRAM_CHAT_ID (optional)"
    else
        echo "❌ .env.example not found"
        exit 1
    fi
fi

# Check Python dependencies
echo "🔍 Checking Python dependencies..."
if ! python -c "import fastapi, motor, pandas, numpy" 2>/dev/null; then
    echo "❌ Some dependencies are missing"
    echo "Installing requirements..."
    pip install -r requirements.txt
fi
echo "✅ Dependencies are installed"

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the application
echo "🌟 Starting FastAPI application..."
echo "📊 Dashboard will be available at: http://localhost:8000"
echo "🔌 WebSocket endpoint: ws://localhost:8000/ws/signals"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Run with uvicorn in development mode
if [ "$1" = "dev" ]; then
    echo "🔧 Running in DEVELOPMENT mode..."
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level info
elif [ "$1" = "prod" ]; then
    echo "🚀 Running in PRODUCTION mode..."
    gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
else
    echo "🔧 Running in DEFAULT mode..."
    python main.py
fi 