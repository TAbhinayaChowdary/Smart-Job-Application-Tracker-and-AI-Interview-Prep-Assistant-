from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from backend.app.core.database import get_db
from backend.app.models.job import JobApplication, InterviewPrep
from backend.app.services.ai_prep import generate_interview_prep

router = APIRouter()

class PrepRequest(BaseModel):
    job_id: int
    resume_text: Optional[str] = None # Optional override if not in job
    job_description: Optional[str] = None # Allow updating JD on the fly

@router.post("/generate/{job_id}")
def generate_prep(job_id: int, request: PrepRequest, db: Session = Depends(get_db)):
    job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update JD if provided
    if request.job_description:
        job.job_description = request.job_description
        db.commit() # Save the new JD for future use
        db.refresh(job)

    # Use resume from request or job
    resume = request.resume_text or job.resume_text
    
    if not job.job_description:
         raise HTTPException(status_code=400, detail="Job Description is missing for this application.")
         
    if not resume:
         raise HTTPException(status_code=400, detail="Resume text is missing. Please provide it.")

    # Call AI Service
    try:
        ai_result = generate_interview_prep(
            role_title=job.role_title,
            company=job.company_name,
            job_description=job.job_description,
            resume_text=resume
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Generation Failed: {str(e)}")
    
    if not ai_result:
        raise HTTPException(status_code=500, detail="Failed to generate prep material.")
    
    # Save to DB
    # Check if exists first
    db_prep = db.query(InterviewPrep).filter(InterviewPrep.job_application_id == job_id).first()
    if db_prep:
        db_prep.generated_notes = ai_result.get("generated_notes", "")
        db_prep.key_topics = str(ai_result.get("key_topics", []))
        db_prep.likely_questions = str(ai_result.get("likely_questions", []))
    else:
        db_prep = InterviewPrep(
            job_application_id=job_id,
            generated_notes=ai_result.get("generated_notes", ""),
            key_topics=str(ai_result.get("key_topics", [])),
            likely_questions=str(ai_result.get("likely_questions", []))
        )
        db.add(db_prep)
    
    db.commit()
    return ai_result
