from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

# --- Authentication and User Data ---

class User(BaseModel):
    """Model for authenticated user data."""
    id: str = Field(..., description="Unique ID for the user (Google ID).")
    email: str
    name: str

class ResumeUpload(BaseModel):
    """Model for accepting resume data."""
    user_id: str
    resume_text: str

# --- Application and Scheduling Data ---

class Application(BaseModel):
    """Model for a single job application/interview event."""
    app_id: str
    user_id: str
    company: str
    role: str
    jd_text: str = Field(..., description="Full text of the Job Description.")
    date: datetime
    status: str = Field(default="Upcoming")

class ApplicationList(BaseModel):
    """Model for listing all applications."""
    applications: List[Application]

# --- AI Preparation Data ---

class PrepTipsResponse(BaseModel):
    """Model for the structured JSON output from the OpenAI API."""
    key_topics_to_revise: List[str] = Field(..., description="Topics the user should study before the interview.")
    likely_behavioral_questions: List[str] = Field(..., description="STAR method questions personalized to the resume.")
    likely_technical_questions: List[str] = Field(..., description="Technical questions based on the JD and Resume.")
    match_confidence: float = Field(..., description="Compatibility score between 0.0 and 1.0.")
    match_feedback: str = Field(..., description="Natural language justification for the confidence score.")

class AIPrepRequest(BaseModel):
    """Model for the request to trigger AI analysis."""
    app_id: str
    user_id: str
