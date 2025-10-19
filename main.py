import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services import auth, gmail_calendar, ai_prep # Import routers/services
from app.core.config import settings

# Initialize FastAPI App
app = FastAPI(
    title="Smart Job Application Tracker API",
    description="Backend for job tracking, scheduling, and AI interview preparation."
)

# --- CORS Middleware (Crucial for Streamlit Communication) ---
# Allows the Streamlit frontend (on a different port/domain) to talk to the backend.
origins = [
    "http://localhost",
    "http://localhost:8501",  # Default Streamlit port
    "http://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(gmail_calendar.router, prefix="/api/scheduler", tags=["Scheduler & Tracking"])
app.include_router(ai_prep.router, prefix="/api/ai", tags=["AI Preparation"])

@app.get("/", tags=["Root"])
async def read_root():
    """Simple health check endpoint."""
    return {"message": "Smart Job Tracker API is running!"}

# Note: Uvicorn typically runs via the command line for production
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
