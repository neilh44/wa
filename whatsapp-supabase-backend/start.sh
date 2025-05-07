#!/bin/bash
# Startup script for WhatsApp to Supabase API

# Load environment variables
set -a
source .env
set +a

# Create required directories
mkdir -p logs whatsapp_data

# Start the application
echo "Starting WhatsApp to Supabase API..."
python -m uvicorn app.main:app --host $APP_HOST --port $APP_PORT --reload
