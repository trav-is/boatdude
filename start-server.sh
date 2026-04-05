#!/bin/bash
# The Boat Dude - Server Management Script

PORT=${1:-8000}
PID_FILE=".server.pid"

start_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "🚤 Server already running on port $PORT (PID: $PID)"
            echo "🌐 URL: http://localhost:$PORT"
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    echo "🚀 Starting The Boat Dude server on port $PORT..."
    python3 server.py "$PORT" &
    echo $! > "$PID_FILE"
    
    # Give it a moment to start
    sleep 2
    
    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "✅ Server started successfully!"
        echo "🌐 URL: http://localhost:$PORT"
        echo "📁 Serving: $(pwd)"
        echo "⏹️  Run './start-server.sh stop' to stop the server"
    else
        echo "❌ Failed to start server"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "🛑 Stopping server (PID: $PID)..."
            kill "$PID"
            rm -f "$PID_FILE"
            echo "✅ Server stopped"
        else
            echo "❌ Server not running"
            rm -f "$PID_FILE"
        fi
    else
        echo "❌ No server PID file found"
    fi
}

status_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ Server is running (PID: $PID)"
            echo "🌐 URL: http://localhost:$PORT"
        else
            echo "❌ Server is not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
    else
        echo "❌ Server is not running"
    fi
}

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 1
        start_server
        ;;
    status)
        status_server
        ;;
    *)
        echo "The Boat Dude - Server Management"
        echo ""
        echo "Usage: $0 {start|stop|restart|status} [port]"
        echo ""
        echo "Commands:"
        echo "  start    Start the server (default port: 8000)"
        echo "  stop     Stop the server"
        echo "  restart  Restart the server"
        echo "  status   Check server status"
        echo ""
        echo "Examples:"
        echo "  $0 start        # Start on port 8000"
        echo "  $0 start 3000   # Start on port 3000"
        echo "  $0 stop         # Stop the server"
        echo "  $0 status       # Check if running"
        exit 1
        ;;
esac


