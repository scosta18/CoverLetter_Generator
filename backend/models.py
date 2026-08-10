from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

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

    experiences = relationship("Experience", back_populates="owner")

class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    skills = Column(String, nullable=True)

    owner = relationship("User", back_populates="experiences")