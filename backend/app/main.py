from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path # Import Path

from backend.app import models
from backend.app.database import engine
from backend.app.api import chat # Import the chat router
from backend.app.api import prompts # Will be imported when prompts API is created

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

# Serve static files (like CSS, JS) from the 'static' directory within the 'frontend' folder
app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent.parent / "frontend" / "static"), name="static")

# Include API routers
# This registers the endpoints defined in chat.py (and prompts.py when it's ready)
app.include_router(chat.router, prefix="/api")
app.include_router(prompts.router, prefix="/api") # Uncomment when prompts API is ready

# Root endpoint to serve the frontend HTML
@app.get("/", response_class=HTMLResponse, summary="Serve Frontend", description="Serves the main frontend HTML application.")
async def serve_frontend():
    """Serves the index.html file for the frontend application."""
    # Construct the path to index.html relative to the current file (main.py)
    html_file_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
    if not html_file_path.is_file():
        raise HTTPException(status_code=500, detail="index.html not found at expected path.")
    with open(html_file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())