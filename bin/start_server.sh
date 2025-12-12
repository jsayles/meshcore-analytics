#!/bin/bash
# MeshCore METRO - Server Start Script

# Get to project directory
cd "$(dirname "$0")/.."

# Check if SSL certificates exist
if [ ! -f "ssl/key.pem" ] || [ ! -f "ssl/cert.pem" ]; then
    echo "Error: SSL certificates not found. Please run bin/pi_install.sh first."
    exit 1
fi

echo "Starting MeshCore METRO server with HTTPS..."
echo ""
echo "Server will be available at:"
echo "  https://$(hostname).local:8443/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start daphne with HTTPS
uv run daphne -e ssl:8443:privateKey=ssl/key.pem:certKey=ssl/cert.pem metro.asgi:application
