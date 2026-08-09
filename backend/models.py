from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base
from pydantic import BaseModel as PydanticBaseModel

class CoverLetterEntry(Base):
    __tablename__ = "Cover_letter"

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String, nullable=True)
    job_description = Column(String, nullable=True)
    company_name = Column(String, nullable = True)
    generated_letter = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class JobInfo(PydanticBaseModel):
    job_title: str
    company_name: str


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)