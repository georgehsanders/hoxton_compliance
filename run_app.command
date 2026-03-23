#!/bin/bash
# Hotel Compliance Tracker — Mac launcher
# Double-click this file to start the app and open it in your browser.

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install dependencies if needed
pip install -q -r requirements.txt 2>/dev/null

echo "Starting Hotel Compliance Tracker..."
echo "The app will open in your browser at http://localhost:5000"
echo "Press Ctrl+C to stop the server."
echo ""

# Open browser after a short delay
(sleep 2 && open "http://localhost:5000") &

# Start the Flask app
python run.py
