import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from google import genai
from typing import List

from database import engine, SessionLocal, Base
from models import CoverLetterEntry
from schemas import JobDescriptionInput, CoverLetterResponse

load_dotenv()
Base.metadata.create_all(bind=engine)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def read_resume() -> str:
    with open("testsubjects/resume.txt", "r", encoding="utf-8") as f:
        return f.read()

def generate_letter_text(resume:str, job_description: str) -> str:
    prompt = f"""You are a professional cover letter writer. Write a concise,
    compelling cover letter tailored to the job description below, using the
    candidate's background. Do not invent experience, skills, or personal details
    (name, email, address, etc.) that are not present in the background text —
    if contact details aren't provided, use placeholders like [Your Name],
    [Your Email]. Use a professional but natural tone, no clichés. Keep it to
    roughly 300-350 words, fitting on one page.
    
    CANDIDATE BACKGROUND:
    {resume}
    
    JOB DESCRIPTION:
    {job_description}
    
    FORMAT:
    1. Sender's contact details (from the background text, or placeholders if missing)
    2. Date
    3. Company name and address (from the job description, or placeholder if missing)
    4. Salutation (use "Dear Hiring Manager," if no specific name is given)
    5. Body: 2-3 paragraphs connecting the candidate's background to the role
    6. Closing line + signature ("Sincerely, [Your Name]")
    
    Write only the letter itself — no subject line, no extra commentary."""
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt
    )
    return response.text


@app.post("/api/cover-letters", response_model=CoverLetterResponse, status_code=201)
def create_cover_letter(payload: JobDescriptionInput, db: Session = Depends(get_db)):
    resume = read_resume()
    letter = generate_letter_text(resume, payload.job_description)
    entry = CoverLetterEntry(
        job_description=payload.job_description,
        generated_letter=letter
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@app.get("/api/cover-letters", response_model=List[CoverLetterResponse])
def list_cover_letters(db:Session = Depends(get_db)):
    return db.query(CoverLetterEntry).order_by(CoverLetterEntry.id.desc()).all()

@app.get("/api/cover-letters/{letter_id}", response_model=CoverLetterResponse)
def get_cover_letter(letter_id: int, db: Session = Depends(get_db)):
    entry = db.query(CoverLetterEntry).filter(CoverLetterEntry.id == letter_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    return entry