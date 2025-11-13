#!/bin/bash

# Exit on any error
set -e

# Define paths
PROJECT_DIR="/home/administrator/Desktop/Resume"
# PROJECT_DIR="/c/Work/Resume Builder/Resume"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Log file
LOGFILE="$PROJECT_DIR/startup.log"
echo "Starting Resume app at $(date)" >> "$LOGFILE"

# --- Start backend ---
cd "$BACKEND_DIR"
source venv/bin/activate
nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 >> "$LOGFILE" 2>&1 &

# --- Start frontend ---
cd "$FRONTEND_DIR"
nohup npm start >> "$LOGFILE" 2>&1 &

echo "Resume app started successfully." >> "$LOGFILE"
