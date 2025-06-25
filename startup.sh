#!/bin/bash
# Navigate to the backend application directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI application using uvicorn on port 9000
uvicorn app.main:app --host 0.0.0.0 --port 9000