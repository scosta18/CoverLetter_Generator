from pydantic import BaseModel
from datetime  import datetime

class JobDescriptionInput(BaseModel):
    job_description : str

class CoverLetterResponse(BaseModel):
    id: int
    job_desription: str
    generated_letter: str
    created_at: datetime

    class Config:
        from_attributes = True