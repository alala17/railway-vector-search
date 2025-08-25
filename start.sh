#!/bin/bash
# Railway typically assigns port 8080, so let's use that directly
echo "Starting application on port 8080"
exec gunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 120 app:app
