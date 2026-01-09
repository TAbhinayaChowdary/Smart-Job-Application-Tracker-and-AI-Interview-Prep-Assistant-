from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import json

from backend.app.core.config import settings


router = APIRouter()

# Allow HTTP for local dev
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CLIENT_SECRETS_FILE = "backend/client_secret.json"
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar"
]

user_credentials = None

def get_google_auth_flow(state=None, redirect_uri=None):
    """Helper to create Flow from either env vars or file"""
    redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
    
    # Priority 1: Env Vars
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
                "javascript_origins": ["http://localhost:8501", "http://localhost:8000"] 
            }
        }
        return Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            state=state,
            redirect_uri=redirect_uri
        )
    
    # Priority 2: File
    if os.path.exists(CLIENT_SECRETS_FILE):
         return Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=state,
            redirect_uri=redirect_uri
        )
        
    return None

@router.get("/login")
def login(request: Request):
    flow = get_google_auth_flow()
    if not flow:
        return {"error": "Google credentials not found. Please check .env or backend/client_secret.json"}
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    request.session['state'] = state
    return RedirectResponse(authorization_url)

@router.get("/callback")
def callback(request: Request):
    global user_credentials
    state = request.session.get('state')
    
    if not state:
         raise HTTPException(status_code=400, detail="State missing in session")

    try:
        flow = get_google_auth_flow(state=state)
        if not flow:
             return {"error": "Credentials missing during callback"}
        
        # Manually force the redirect_uri to match what was used in generation
        # because fetch_token is strict about it.
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        flow.fetch_token(authorization_response=str(request.url))

        
        credentials = flow.credentials
        user_credentials = credentials
        
        # Save credentials to file for persistence across restarts (Optional but good)
        # with open('token.json', 'w') as token:
        #     token.write(credentials.to_json())

        return RedirectResponse("http://localhost:8501")
    except Exception as e:
        print(f"Auth Error: {e}")
        return {"error": str(e)}

@router.get("/me")
def get_current_user():
    global user_credentials
    if not user_credentials or not user_credentials.valid:
        return None
    
    try:
        service = build('oauth2', 'v2', credentials=user_credentials)
        user_info = service.userinfo().get().execute()
        return user_info
    except Exception as e:
        return None

@router.get("/logout")
def logout(request: Request):
    global user_credentials
    user_credentials = None
    request.session.clear()
    return {"message": "Logged out"}
