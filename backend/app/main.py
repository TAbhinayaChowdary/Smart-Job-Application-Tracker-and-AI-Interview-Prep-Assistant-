from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.app.core.database import engine, Base
from backend.app.core.config import settings
from backend.app.api import jobs, auth, prep, gmail_routes, resumes, calendar_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SJTAP API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    print("Startup: Registered Routes:")
    for route in app.routes:
        print(f" - {route.path} [{route.name}]")

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(prep.router, prefix="/prep", tags=["prep"])
app.include_router(gmail_routes.router, prefix="/gmail", tags=["gmail"])
app.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
app.include_router(calendar_routes.router, prefix="/calendar", tags=["calendar"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Job Application Tracker API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
