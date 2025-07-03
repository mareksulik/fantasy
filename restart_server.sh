#!/bin/bash
# Proper server restart script

# Kill existing process
echo "Stopping existing server..."
pkill -f "python app.py" 2>/dev/null || true
sleep 1

# Find and kill by port if still running
lsof -ti:8086 | xargs kill -9 2>/dev/null || true
sleep 1

# Start server with nohup
echo "Starting server..."
cd /Users/mareksulik/Documents/GitHub/fantasy
source venv/bin/activate && nohup python app.py > app.log 2>&1 &

sleep 2
echo "Server started on http://localhost:8086"
echo "Check logs: tail -f app.log"