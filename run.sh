#!/bin/bash

# MindAware Agent - Startup Script
# This script launches both the backend API and frontend dashboard

set -e

echo "🧠 MindAware Agent - Starting..."
echo "================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip3 install -r requirements.txt --quiet

# Install frontend dependencies
echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
cd ui/frontend
npm install --silent
cd ../..

# Create logs directory
mkdir -p data/logs

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Using defaults.${NC}"
    echo -e "${YELLOW}   For LLM features, set: export OPENAI_API_KEY=sk-...${NC}"
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend server
echo -e "${GREEN}🚀 Starting backend API server on http://localhost:8000${NC}"
cd src/api
python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
sleep 3

# Start frontend dev server
echo -e "${GREEN}🚀 Starting frontend dashboard on http://localhost:5173${NC}"
cd ui/frontend
npm run dev &
FRONTEND_PID=$!
cd ../..

echo ""
echo -e "${GREEN}✅ MindAware Agent is running!${NC}"
echo "================================"
echo -e "Backend API:  ${BLUE}http://localhost:8000${NC}"
echo -e "Frontend UI:  ${BLUE}http://localhost:5173${NC}"
echo -e "API Docs:     ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Run simulation in background (optional)
read -p "Start simulation loop? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🎮 Starting simulation...${NC}"
    python3 src/main.py --scenario fatigue --iterations 20 --interval 3 &
    SIM_PID=$!
fi

# Wait for processes
wait

