#!/bin/bash
# Navigate to the backend application directory
cd backend/app

# Start the FastAPI application using uvicorn on port 9000
uvicorn main:app --host 0.0.0.0 --port 9000