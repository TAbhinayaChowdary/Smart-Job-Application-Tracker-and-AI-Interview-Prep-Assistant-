from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from backend.app.services.gmail_parser import fetch_job_related_emails

router = APIRouter()

@router.get("/scan", response_model=List[Dict[str, Any]])
def scan_gmail_for_jobs(limit: int = Query(50, ge=1, le=100)):
    """
    Scans the user's Gmail for job-related emails.
    Requires the user to be logged in via Google (to have valid credentials).
    """
    try:
        results = fetch_job_related_emails(max_results=limit)
        return results
    except RuntimeError as e:
        # Likely auth error
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
