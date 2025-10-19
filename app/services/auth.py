from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.database import mock_save_user_token 
from google_auth_oauthlib.flow import Flow
#from google_api_python_client.discovery import build
from app.core.database import mock_save_user_token, mock_get_user_token
# ...existing code...

from googleapiclient.discovery import build
# ...existing code...

router = APIRouter()

# --- OAuth Configuration ---
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'openid', 'email', 'profile' # Basic user info
]

CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "project_id": "smart-job-tracker", 
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        # Add the Streamlit port as a JS origin for testing
        "javascript_origins": ["http://127.0.0.1:8000", "http://127.0.0.1:8501"] 
    }
}

# Mock store for OAuth state (for testing purposes)
TEMP_SESSION_STATE = {} 

@router.get("/google/login")
async def login(request: Request):
    """Initiates the Google OAuth 2.0 flow."""
    
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline', # Requests the Refresh Token
        include_granted_scopes='true'
    )
    
    TEMP_SESSION_STATE['oauth_state'] = state
    
    return RedirectResponse(authorization_url)

@router.get("/google/callback")
async def callback(request: Request):
    """Handles the redirect from Google after user grants permission."""
    
    state = request.query_params.get('state')
    
    if state != TEMP_SESSION_STATE.get('oauth_state'):
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="State mismatch.")
    
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials
    
    # Get user info to use as a stable user ID
    user_info_service = build('oauth2', 'v2', credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    user_id = user_info['id']
    
    # CRUCIAL STEP: Save the Refresh Token for long-term, offline access
    if credentials.refresh_token:
        mock_save_user_token(user_id, credentials.refresh_token)
    
    TEMP_SESSION_STATE.pop('oauth_state', None)
    
    return {"message": "Authentication successful!", "user_id": user_id, "name": user_info.get('name')}

@router.get("/user/status")
async def get_user_status(user_id: str = "MOCK_USER_ID"):
    """Mocks checking if the user is logged in/tokens exist."""
    refresh_token = mock_get_user_token(user_id)
    if refresh_token:
        return {"authenticated": True, "message": "User token active."}
    return {"authenticated": False, "message": "User needs to authenticate via OAuth."}
