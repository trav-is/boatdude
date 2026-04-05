#!/bin/bash
# Start both the main server and the API server for The Boat Dude

echo "🚤 Starting The Boat Dude servers..."

# Function to cleanup background processes
cleanup() {
    echo "🛑 Shutting down servers..."
    if [ ! -z "$MAIN_PID" ]; then
        kill $MAIN_PID 2>/dev/null
    fi
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if Python dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import flask, gspread" 2>/dev/null || {
    echo "❌ Missing dependencies. Installing..."
    pip3 install -r requirements.txt
}

# Start the main HTTP server (for the website)
echo "🌐 Starting main server on port 8000..."
python3 server.py 8000 &
MAIN_PID=$!

# Wait a moment for the main server to start
sleep 2

# Start the API server (for Google Sheets integration)
echo "🔗 Starting API server on port 5001..."
cd api
python3 app.py &
API_PID=$!
cd ..

# Wait a moment for the API server to start
sleep 2

echo ""
echo "✅ Servers started successfully!"
echo "🌐 Main site: http://localhost:8000"
echo "🔧 Admin interface: http://localhost:8000/admin/"
echo "🔗 API server: http://localhost:5001"
echo ""
echo "⏹️  Press Ctrl+C to stop both servers"

# Wait for background processes
wait
