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



class CoverLetterResponse(BaseModel):
    id: int
    job_title: str
    company_name: str
    job_description: str
    generated_letter: str
    created_at: datetime

    class Config:
        from_attributes = True