from fastapi import APIRouter
from googleapiclient.discovery import build
import datetime
from backend.app.api.auth import user_credentials

router = APIRouter()

@router.get("/events")
def get_calendar_events():
    global user_credentials
    # In a real production app, credentials should be stored in DB per user and retrieved from request session.
    # Here we use the global variable from auth.py for the single-user local flow.
    from backend.app.api.auth import user_credentials
    
    if not user_credentials or not user_credentials.valid:
        return {"error": "Not authenticated"}

    try:
        service = build('calendar', 'v3', credentials=user_credentials)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=50, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        return events
    except Exception as e:
        return {"error": str(e)}
