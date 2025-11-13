#!/bin/bash

# Exit on any error
set -e

LOGFILE="/home/administrator/Desktop/Resume/startup.log"

echo "Stopping Resume app at $(date)" >> "$LOGFILE"

# Kill backend (uvicorn)
pkill -f "uvicorn main:app" || echo "No backend process found." >> "$LOGFILE"

# Kill frontend (npm start)
pkill -f "npm start" || echo "No frontend process found." >> "$LOGFILE"

echo "Resume app stopped successfully." >> "$LOGFILE"
