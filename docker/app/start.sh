#!/bin/sh
# Startup script for HOPE Bot

# Start webhook in background
echo "Starting webhook server..."
uv run jarvis run service --bind 0.0.0.0:9000 &

# Start Chainlit
echo "Starting Chainlit..."
uv run jarvis run web --bind 0.0.0.0:8000
