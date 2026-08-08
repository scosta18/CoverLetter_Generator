from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class CoverLetterEntry(Base):
    __tablename__ = "Cover_letter"

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String, mutable=True)
    company_name = Column(String, nullable = True)
    generated_letter = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)