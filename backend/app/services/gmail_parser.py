from typing import List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email import message_from_bytes

from backend.app.services.ai_prep import extract_job_details
import backend.app.api.auth as app_auth  # reuse your existing creds


JOB_KEYWORDS = [
    "job application",
    "applied for",
    "interview",
    "technical interview",
    "hr interview",
    "online assessment",
    "coding test",
    "hiring process",
    "shortlisted",
    "selected",
    "rejected",
    "offer letter",
    "recruiter",
    "career opportunity",
    "position",
    "role",
    "recruitment"
]


def _get_gmail_service():
    if not app_auth.user_credentials or not app_auth.user_credentials.valid:
        raise RuntimeError("User is not authenticated with Google or token is invalid.")
    return build("gmail", "v1", credentials=app_auth.user_credentials)


def _get_message(service, msg_id: str) -> Dict:
    return service.users().messages().get(userId="me", id=msg_id, format="full").execute()


def _extract_subject_and_body(msg: Dict) -> Dict[str, str]:
    headers = msg.get("payload", {}).get("headers", [])
    subject = ""
    for h in headers:
        if h.get("name", "").lower() == "subject":
            subject = h.get("value", "")
            break

    # Try to get text/plain body, then text/html
    body = ""
    payload = msg.get("payload", {})
    
    def get_data_from_part(part):
        return base64.urlsafe_b64decode(part.get("body", {}).get("data", "").encode("utf-8")).decode("utf-8", errors="ignore")

    if payload.get("mimeType") == "text/plain":
        body = get_data_from_part(payload)
    
    if not body:
        # Walk parts
        parts = payload.get("parts", []) or []
        # First look for plain text
        for part in parts:
            if part.get("mimeType") == "text/plain":
                body = get_data_from_part(part)
                break
        
        # If no plain text, search purely for HTML (and maybe one day strip tags, or just give raw html to AI)
        if not body:
             for part in parts:
                if part.get("mimeType") == "text/html":
                    body = get_data_from_part(part)
                    break
    
    return {"subject": subject, "body": body}


def _is_job_related(subject: str, body: str) -> bool:
    text = f"{subject}\n{body}".lower()
    return any(kw in text for kw in JOB_KEYWORDS)


def fetch_job_related_emails(max_results: int = 50, page_token: str = None) -> Dict[str, Any]:
    """
    Returns a dict with:
      - emails: list of job-related emails
      - next_page_token: string/None
    """
    service = _get_gmail_service()

    try:
        kwargs = {
            'userId': "me",
            'maxResults': max_results,
        }
        if page_token:
            kwargs['pageToken'] = page_token

        resp = service.users().messages().list(**kwargs).execute()

        messages = resp.get("messages", [])
        next_page = resp.get("nextPageToken")
        
        results: List[Dict] = []

        for m in messages:
            msg = _get_message(service, m["id"])
            parts = _extract_subject_and_body(msg)
            if _is_job_related(parts["subject"], parts["body"]):
                # Extract details using AI
                # Use body if available, otherwise snippet is better than nothing
                content_to_analyze = parts["body"] if len(parts["body"]) > 50 else msg.get("snippet", "")
                extracted = extract_job_details(parts["subject"], content_to_analyze)
                
                results.append(
                    {
                        "id": msg.get("id"),
                        "threadId": msg.get("threadId"),
                        "subject": parts["subject"],
                        "body": parts["body"][:500],  # truncate for response size
                        "snippet": msg.get("snippet"),
                        "internalDate": msg.get("internalDate"),
                        # Extracted fields
                        "role_title": extracted.get("role_title"),
                        "company_name": extracted.get("company_name"),
                        "status": extracted.get("status"),
                        "interview_date": extracted.get("interview_date"),
                        "deadline_date": extracted.get("deadline_date"),
                        "confidence": extracted.get("confidence"),
                        "link": f"https://mail.google.com/mail/u/0/#inbox/{msg.get('threadId')}"
                    }
                )

        return {
            "emails": results,
            "next_page_token": next_page
        }

    except HttpError as e:
        raise RuntimeError(f"Gmail API error: {e}")
