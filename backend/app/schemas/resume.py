from pydantic import BaseModel
from datetime import datetime

class ResumeBase(BaseModel):
    name: str
    content: str

class ResumeCreate(ResumeBase):
    pass

class Resume(ResumeBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
