#!/bin/bash

# Start PulseAudio in system-wide mode with verbose output suppressed
pulseaudio --verbose --exit-idle-time=-1 --system --disallow-exit -D > /dev/null 2>&1

# Optional: wait a moment for pulseaudio to fully start
sleep 2

# Start the Uvicorn server for the Flask app
uvicorn flask_app:app --host 0.0.0.0 --port "${PORT:-8000}"
