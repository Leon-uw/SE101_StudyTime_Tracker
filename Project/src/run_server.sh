#!/bin/bash
# Helper script to run the Flask server

cd "$(dirname "$0")"
echo "🚀 Starting Flask server..."
echo "📍 Server will be available at: http://127.0.0.1:5000"
echo "⚠️  Keep this terminal window open!"
echo "🛑 Press Ctrl+C to stop the server"
echo ""
python3 app.py
