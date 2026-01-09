from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from backend.app.core.database import Base

class ApplicationStatus(str, enum.Enum):
    APPLIED = "Applied"
    SCREENING = "Screening"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    REJECTED = "Rejected"
    SHOULDAPPLY = "Should Apply"

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    role_title = Column(String, index=True)
    company_name = Column(String, index=True)
    job_description = Column(Text, nullable=True)
    resume_text = Column(Text, nullable=True) # Or file path
    status = Column(String, default=ApplicationStatus.APPLIED)
    application_date = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    # Relationship to InterviewPrep
    prep_materials = relationship("InterviewPrep", back_populates="application", uselist=False)

class InterviewPrep(Base):
    __tablename__ = "interview_preps"
    
    id = Column(Integer, primary_key=True, index=True)
    job_application_id = Column(Integer, ForeignKey("job_applications.id"))
    
    generated_notes = Column(Text)
    key_topics = Column(Text) # Could be JSON
    likely_questions = Column(Text) # Could be JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    application = relationship("JobApplication", back_populates="prep_materials")
