from pydantic import BaseModel
from datetime  import datetime

class JobDescriptionInput(BaseModel):
    job_description : str

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ExperienceCreate(BaseModel):
    title: str
    company_name: str | None = None
    description: str
    skills: str | None = None

class ExperienceResponse(BaseModel):
    id: int
    title: str
    company_name: str | None
    description: str
    skills: str | None

    class Config:
        from_attributes = True

class SchoolCreate(BaseModel):
    school_name: str
    degree_type: str
    skills: str | None = None
    start_date: str | None = None
    end_date: str | None = None

class SchoolResponse(BaseModel):
    id: int
    school_name: str
    degree_type: str
    skills: str | None
    start_date: str | None
    end_date: str | None

    class Config: 
        from_attributes = True

class CoverLetterResponse(BaseModel):
    id: int
    job_title: str
    company_name: str
    job_description: str
    generated_letter: str
    created_at: datetime

    class Config:
        from_attributes = True