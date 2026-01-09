from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.job import IgnoredEmail
from backend.app.services.gmail_parser import fetch_job_related_emails

router = APIRouter()

@router.get("/scan", response_model=Dict[str, Any])
def scan_gmail_for_jobs(
    limit: int = Query(50, ge=1, le=100), 
    page_token: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Scans the user's Gmail for job-related emails.
    Requires the user to be logged in via Google (to have valid credentials).
    Filters out previously ignored emails.
    Returns:
      {
        "emails": [...],
        "next_page_token": "..."
      }
    """
    try:
        # Fetch ignored IDs (cache this?)
        ignored_ids = {i.message_id for i in db.query(IgnoredEmail.message_id).all()}
        
        # Pass page_token down
        data = fetch_job_related_emails(max_results=limit, page_token=page_token)
        raw_emails = data.get("emails", [])
        next_token = data.get("next_page_token")
        
        # Filter
        filtered_emails = [r for r in raw_emails if r['id'] not in ignored_ids]
        
        return {
            "emails": filtered_emails,
            "next_page_token": next_token
        }
    except RuntimeError as e:
        # Likely auth error
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ignore/{message_id}")
def ignore_email(message_id: str, db: Session = Depends(get_db)):
    """
    Marks an email as ignored so it doesn't show up in future scans.
    """
    try:
        existing = db.query(IgnoredEmail).filter(IgnoredEmail.message_id == message_id).first()
        if not existing:
            new_ignore = IgnoredEmail(message_id=message_id)
            db.add(new_ignore)
            db.commit()
        return {"message": "Email ignored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
