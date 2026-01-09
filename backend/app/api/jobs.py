from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.database import get_db
from backend.app.models.job import JobApplication
from backend.app.schemas.job import JobApplicationCreate, JobApplication as JobApplicationSchema
from backend.app.services.web_scraper import scrape_job_from_url
from pydantic import BaseModel

router = APIRouter()

class UrlRequest(BaseModel):
    url: str

@router.post("/parse-url")
def parse_job_url(request: UrlRequest):
    result = scrape_job_from_url(request.url)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/", response_model=JobApplicationSchema)
def create_job(job: JobApplicationCreate, db: Session = Depends(get_db)):
    try:
        db_job = JobApplication(**job.dict())
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/", response_model=List[JobApplicationSchema])
def read_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    jobs = db.query(JobApplication).offset(skip).limit(limit).all()
    return jobs

@router.get("/{job_id}", response_model=JobApplicationSchema)
def read_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
