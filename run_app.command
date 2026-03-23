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

# Port 5000 is used by macOS AirPlay Receiver — use 5050 instead
PORT="${PORT:-5050}"

echo "Starting Hotel Compliance Tracker..."
echo "The app will open in your browser at http://localhost:$PORT"
echo "Press Ctrl+C to stop the server."
echo ""

# Start the Flask app in the background, keeping stdout/stderr visible
PORT=$PORT python run.py 2>&1 &
APP_PID=$!

# Wait until the server is actually accepting connections
echo "Waiting for server to start..."
ATTEMPT=0
MAX_ATTEMPTS=50
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))

    # Stop waiting if the app process died
    if ! kill -0 $APP_PID 2>/dev/null; then
        echo "Error: Flask app failed to start."
        exit 1
    fi

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT" 2>&1)
    CURL_EXIT=$?

    if [ $CURL_EXIT -eq 0 ] && [ "$HTTP_CODE" = "200" ]; then
        break
    fi

    sleep 0.3
done

if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
    echo "Error: server did not respond after $MAX_ATTEMPTS attempts."
    exit 1
fi

echo "Server is ready — opening browser."
open "http://localhost:$PORT"

# Bring Flask back to the foreground so Ctrl+C stops it
wait $APP_PID
