from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app import models
from backend.app.database import engine
from backend.app.api import chat # Import the chat router
# from backend.app.api import prompts # Will be imported when prompts API is created

# Initialize FastAPI app
app = FastAPI(
    title="PromptCraft AI Chat Backend",
    description="API for managing AI chat conversations and system prompts.",
    version="1.0.0",
)

# Configure CORS middleware
# This allows the frontend (running on a different port/domain) to communicate with the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9000"], # Allow frontend running on port 9000
    allow_credentials=True,
    allow_methods=["*"], # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allow all headers
)

# Event handler for application startup
@app.on_event("startup")
def on_startup():
    """Create database tables on application startup."""
    # This will create all tables defined in models.py if they don't already exist.
    models.Base.metadata.create_all(bind=engine)

# Include API routers
# This registers the endpoints defined in chat.py (and prompts.py when it's ready)
app.include_router(chat.router, prefix="/api")
# app.include_router(prompts.router, prefix="/api") # Uncomment when prompts API is ready

# Root endpoint for health check
@app.get("/", summary="Health Check", description="Checks if the API is running.")
async def root():
    """Root endpoint returning a simple message for health check."""
    return {"message": "PromptCraft AI Chat API is running!"}