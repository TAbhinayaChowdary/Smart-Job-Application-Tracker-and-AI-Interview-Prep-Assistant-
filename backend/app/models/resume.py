from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from backend.app.core.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # User friendly name or filename
    content = Column(Text) # Text content of the resume
    created_at = Column(DateTime(timezone=True), server_default=func.now())
