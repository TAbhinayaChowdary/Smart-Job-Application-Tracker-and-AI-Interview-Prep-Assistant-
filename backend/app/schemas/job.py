from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class JobApplicationBase(BaseModel):
    role_title: str
    company_name: str
    job_description: Optional[str] = None
    resume_text: Optional[str] = None
    status: Optional[str] = "Applied"
    source: Optional[str] = None
    location: Optional[str] = None
    interview_date: Optional[datetime] = None
    deadline_date: Optional[datetime] = None

class JobApplicationCreate(JobApplicationBase):
    job_description: Optional[str] = None
    resume_text: Optional[str] = None

class JobApplication(JobApplicationBase):
    id: int
    application_date: datetime

    class Config:
        from_attributes = True
