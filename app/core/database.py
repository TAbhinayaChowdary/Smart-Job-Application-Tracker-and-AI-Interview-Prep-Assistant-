from app.core.config import settings
from typing import Generator
import time
import random
# --- MOCK DATABASE IMPLEMENTATION ---
# A dictionary to simulate storing user tokens, resumes, and job data
MOCK_DB_STORE = {
    "users": {}, # {user_id: {refresh_token: str, resume_text: str}}
    "applications": {} # {app_id: {user_id: str, company: str, jd_text: str, date: str}}
}

# --- Mock Connection Functions ---

def get_db() -> Generator:
    """Dependency injector for database session/connection."""
    # Simulate opening a connection
    try:
        time.sleep(0.01) 
        yield MOCK_DB_STORE
    finally:
        pass
        
# --- Mock Data CRUD Operations ---

def mock_save_user_token(user_id: str, refresh_token: str):
    """Simulates saving a user's refresh token and state."""
    if user_id not in MOCK_DB_STORE['users']:
        MOCK_DB_STORE['users'][user_id] = {}
    MOCK_DB_STORE['users'][user_id]['refresh_token'] = refresh_token
    print(f"--- DB: Refresh token saved for user {user_id} ---")

def mock_get_user_token(user_id: str):
    """Simulates retrieving a user's refresh token."""
    return MOCK_DB_STORE['users'].get(user_id, {}).get('refresh_token')

def mock_get_user_resume(user_id: str):
    """Simulates retrieving a user's resume text."""
    return MOCK_DB_STORE['users'].get(user_id, {}).get('resume_text')

def mock_get_applications(user_id: str):
    """Simulates retrieving all applications for a user."""
    return [
        app_data for app_id, app_data in MOCK_DB_STORE['applications'].items() 
        if app_data['user_id'] == user_id
    ]

def mock_add_application(user_id: str, company: str, role: str, jd_text: str, interview_date: str):
    """Mocks adding a new application to the DB (simulating Gmail service)."""
    import time # Needed here since we use it
    app_id = f"APP-{int(time.time())}-{random.randint(100,999)}"
    MOCK_DB_STORE['applications'][app_id] = {
        "user_id": user_id,
        "app_id": app_id,
        "company": company,
        "role": role,
        "jd_text": jd_text,
        "date": interview_date,
        "status": "Upcoming"
    }
    return MOCK_DB_STORE['applications'][app_id]
