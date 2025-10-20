import os 
# --- FIX for InsecureTransportError during local development ---
# The OAuth library strictly requires HTTPS for the token exchange.
# Since we are running locally on http://127.0.0.1, we must explicitly set 
# this flag to allow insecure transport for testing purposes only.
if not os.environ.get("OAUTHLIB_INSECURE_TRANSPORT"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
# -------------------------------------------------------------

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.database import mock_save_user_token 
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from app.core.database import mock_save_user_token, mock_get_user_token

router = APIRouter()

# --- OAuth Configuration ---
# --- FIX APPLIED HERE: Using canonical (long-form) scope URLs to ensure exact match ---
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'openid', 
    'https://www.googleapis.com/auth/userinfo.email', 
    'https://www.googleapis.com/auth/userinfo.profile'
]
# ---------------------------------------------------------------------------------------

CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "project_id": "smart-job-tracker-475513", 
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": settings.GOOGLE_CLIENT_SECRET, # This is the critical line
        "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        # Add the Streamlit port as a JS origin for testing
        "javascript_origins": ["http://127.0.0.1:8000", "http://127.0.0.1:8501"] 
    }
}

# Mock store for OAuth state (for testing purposes)
TEMP_SESSION_STATE = {} 

# --- DEBUGGING STEP ADDED HERE ---
# Check if the secret key length is plausible (40 characters for most Google OAuth secrets)
# This will show a printout when the FastAPI server starts.
if len(settings.GOOGLE_CLIENT_SECRET) < 30 or settings.GOOGLE_CLIENT_SECRET.startswith('dummy'):
    print("--- WARNING: GOOGLE_CLIENT_SECRET appears to be UNSET or DUMMY. Check .env file! ---")
else:
    print(f"--- INFO: GOOGLE_CLIENT_SECRET is loaded (length: {len(settings.GOOGLE_CLIENT_SECRET)}). ---")
# -----------------------------------


@router.get("/google/login")
async def login(request: Request):
    """Initiates the Google OAuth 2.0 flow."""
    
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    
    # --- CHANGE 1: Force re-consent to ensure refresh token is always sent, and cache is bypassed ---
    authorization_url, state = flow.authorization_url(
        access_type='offline', # Requests the Refresh Token
        include_granted_scopes='true',
        prompt='consent' # Forces the user to see the consent screen every time
    )
    # ------------------------------------------------------------------------------------------------

    TEMP_SESSION_STATE['oauth_state'] = state
    
    return RedirectResponse(authorization_url)

@router.get("/google/callback")
async def callback(request: Request):
    """Handles the redirect from Google after user grants permission."""
    
    state = request.query_params.get('state')
    
    if state != TEMP_SESSION_STATE.get('oauth_state'):
         # If the state is not found (server was restarted), guide the user
         print("--- ERROR: STATE MISMATCH OR SERVER RESTARTED ---")
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST, 
             detail="State mismatch. Please try signing in again from the Streamlit dashboard."
         )
    
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    
    try:
        flow.fetch_token(authorization_response=str(request.url))
    except Exception as e:
        # --- CHANGE 2: Print the specific error from the OAuth library to the console ---
        print(f"--- FATAL OAUTH ERROR during fetch_token: {e} ---")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving access tokens from Google. Check FastAPI logs for details."
        )

    credentials = flow.credentials
    
    # Get user info to use as a stable user ID
    user_info_service = build('oauth2', 'v2', credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    user_id = user_info['id']
    user_name = user_info.get('name', 'User') # Get user name
    
    # CRUCIAL STEP: Save the Refresh Token for long-term, offline access
    if credentials.refresh_token:
        mock_save_user_token(user_id, credentials.refresh_token)
    
    TEMP_SESSION_STATE.pop('oauth_state', None)
    
    # --- FINAL CHANGE: Redirect the user back to the Streamlit app URL ---
    # We must construct the Streamlit URL (port 8501) and pass the retrieved user info 
    # as query parameters so Streamlit (app.py) can read it and update the session state.
    
    # Define the Streamlit base URL
    STREAMLIT_BASE_URL = "http://127.0.0.1:8501"
    
    # Construct the query parameters to pass user info back to the frontend
    # We pass the user_id and name so Streamlit knows who logged in.
    redirect_params = {
        "user_id": user_id,
        "user_name": user_name,
        "auth_success": "true" # Flag for Streamlit to know authentication worked
    }
    
    redirect_url = f"{STREAMLIT_BASE_URL}?{__import__('urllib.parse').parse.urlencode(redirect_params)}"
    
    # The response is now a redirect, not the JSON message.
    return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    # ----------------------------------------------------------------------


@router.get("/user/status")
async def get_user_status(user_id: str = "MOCK_USER_ID"):
    """Mocks checking if the user is logged in/tokens exist."""
    refresh_token = mock_get_user_token(user_id)
    if refresh_token:
        return {"authenticated": True, "message": "User token active."}
    return {"authenticated": False, "message": "User needs to authenticate via OAuth."}
