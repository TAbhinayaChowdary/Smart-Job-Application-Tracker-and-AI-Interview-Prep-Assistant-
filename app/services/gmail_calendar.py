from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Body, Path
from app.models.schemas import ApplicationList, Application, ResumeUpload
from app.core.database import mock_get_user_token, mock_add_application, mock_get_applications, mock_get_user_resume, MOCK_DB_STORE
from app.models.schemas import User
from datetime import datetime, timedelta
import random
import time
from typing import Dict

router = APIRouter()

# --- MOCK JOB DESCRIPTIONS ---
MOCK_JDS: Dict[str, str] = {
    "JD-001": "Senior Backend Engineer role requires 5+ years experience in Python, FastAPI, and PostgreSQL. Must be proficient in REST/gRPC, Docker, and Kubernetes deployment. Deep understanding of cloud-native architecture (AWS) is crucial.",
    "JD-002": "Junior Data Scientist opening focusing on statistical modeling, predictive analysis using scikit-learn and pandas. Experience with data visualization (Matplotlib) is a plus. Basic SQL knowledge required.",
    "JD-003": "DevOps Associate opening for freshers. Focus on CI/CD pipelines, Git, and basic system administration on Linux. Cloud experience is not mandatory but highly preferred.",
    "JD-004": "SDE Intern requiring strong foundational knowledge in data structures and algorithms, primarily in Java or Python. Exposure to web development frameworks (like Streamlit!) is beneficial."
}

# --- BACKGROUND TASK: AUTOMATED CHECKER ---

def check_gmail_and_schedule(user_id: str):
    """
    SIMULATED background task that periodically checks Gmail and schedules events.
    In production, this would use a scheduler (e.g., Celery).
    """
    refresh_token = mock_get_user_token(user_id)
    if not refresh_token:
        print(f"[{user_id}] Checker: Token not found, skipping check.")
        return

    print(f"[{user_id}] Checker: Starting Gmail check...")
    
    # 1. Exchange Refresh Token for Access Token
    # 2. Call Gmail API (Look for emails matching subject/body keywords)
    # 3. Use NLP/Heuristics to parse Date, Time, Company, and JD Text
    
    time.sleep(1) # Simulate API latency
    if random.random() < 0.5: # 50% chance of finding a new email
        new_app_data = {
            "company": random.choice(["MegaCorp", "AlphaTech", "GlobalSoft"]),
            "role": random.choice(["Software Engineer", "Data Analyst", "Intern"]),
            "jd_text": random.choice(list(MOCK_JDS.values())),
            "interview_date": (datetime.now() + timedelta(days=random.randint(3, 10))).isoformat()
        }

        # 4. Simulate Database Save
        new_app = mock_add_application(
            user_id=user_id,
            company=new_app_data['company'],
            role=new_app_data['role'],
            jd_text=new_app_data['jd_text'],
            interview_date=new_app_data['interview_date']
        )

        # 5. Call Google Calendar API (Create event with 24h and 1h reminders)
        print(f"[{user_id}] Checker: ✅ New Interview Found and Scheduled: {new_app['company']}!")
    else:
        print(f"[{user_id}] Checker: No new interview emails found.")


# --- API ENDPOINTS ---

@router.post("/start-check")
async def start_background_check(user: User, background_tasks: BackgroundTasks):
    """Endpoint to trigger the asynchronous Gmail check for new interviews."""
    background_tasks.add_task(check_gmail_and_schedule, user.id)
    return {"message": "Background Gmail check initiated."}

@router.get("/applications/{user_id}", response_model=ApplicationList)
async def get_applications_list(user_id: str):
    """Retrieves all tracked applications/interviews for the user."""
    
    # Add initial mock data if the DB is empty (for Streamlit demo initialization)
    if not mock_get_applications(user_id):
        mock_add_application(user_id, "TechCorp Solutions", "Senior Backend Engineer", MOCK_JDS["JD-001"], (datetime.now() + timedelta(days=2, hours=3)).isoformat())
        mock_add_application(user_id, "Innovate Systems", "Junior Data Scientist", MOCK_JDS["JD-002"], (datetime.now() + timedelta(days=5, hours=1)).isoformat())
        mock_add_application(user_id, "Aurora Labs", "SDE Intern", MOCK_JDS["JD-004"], (datetime.now() + timedelta(days=15, hours=5)).isoformat())

    app_data = mock_get_applications(user_id)
    
    # Convert ISO string date back to datetime objects for Pydantic validation
    for app in app_data:
        app['interview_date'] = datetime.fromisoformat(app['interview_date'])
        
    return ApplicationList(applications=app_data)

@router.post("/mock-save-resume/{user_id}")
async def mock_save_resume_endpoint(
    user_id: str = Path(..., description="User ID"),
    data: ResumeUpload = Body(...)
):
    """Mocks saving the resume text from the Streamlit frontend."""
    # This endpoint is strictly for the Streamlit demo integration to save the resume text
    if user_id not in MOCK_DB_STORE['users']:
        MOCK_DB_STORE['users'][user_id] = {}
    MOCK_DB_STORE['users'][user_id]['resume_text'] = data.resume_text
    return {"message": "Mock resume saved successfully."}
