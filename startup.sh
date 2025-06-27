#!/bin/bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Remove the old database file to ensure schema is up-to-date
rm -f ./sql_app.db

# Start the FastAPI application using uvicorn on port 9000
# Run from the project root so that 'backend' is a discoverable package
uvicorn backend.app.main:app --host 0.0.0.0 --port 9000