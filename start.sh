#!/bin/bash
# Get port from environment variable or default to 8080
PORT=${PORT:-8080}
echo "Starting application on port $PORT"
exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app
