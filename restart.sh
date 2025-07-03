#!/bin/bash
pkill -f "python app.py" 2>/dev/null
sleep 1
cd /Users/mareksulik/Documents/GitHub/fantasy
source venv/bin/activate
nohup python app.py > app.log 2>&1 &
echo "Server restarted on http://localhost:8086"