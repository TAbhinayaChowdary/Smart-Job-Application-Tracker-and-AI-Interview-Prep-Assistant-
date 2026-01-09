from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.resume import Resume
from backend.app.schemas.resume import ResumeCreate, Resume as ResumeSchema
from typing import List

router = APIRouter()

@router.post("/", response_model=ResumeSchema)
def create_resume(resume: ResumeCreate, db: Session = Depends(get_db)):
    db_resume = Resume(name=resume.name, content=resume.content)
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume

@router.get("/", response_model=List[ResumeSchema])
def get_resumes(db: Session = Depends(get_db)):
    return db.query(Resume).order_by(Resume.created_at.desc()).all()

@router.delete("/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    db.delete(resume)
    db.commit()
    return {"ok": True}
