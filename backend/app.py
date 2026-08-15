import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from google import genai
from typing import List

from database import engine, SessionLocal, Base
from models import CoverLetterEntry, JobInfo
from schemas import JobDescriptionInput, CoverLetterResponse

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError

from models import User, CoverLetterEntry, JobInfo
from schemas import UserCreate, Token
from auth import hash_password, verify_password, create_access_token, decode_access_token
from fastapi.responses import Response
from fpdf import FPDF
from fastapi.middleware.cors import CORSMiddleware

from models import Experience, School
from schemas import ExperienceCreate, ExperienceResponse, SchoolCreate, SchoolResponse




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

load_dotenv()
Base.metadata.create_all(bind=engine)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# FastAPI dependency that yields a DB session per-request and closes it afterwards
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# def read_resume() -> str:
#     with open("testsubjects/resume.txt", "r", encoding="utf-8") as f:
#         return f.read()

# Builds a plain-text "resume" for the user from their saved Experience entries,
# to be fed to Gemini as candidate background
def build_resume_text(user: User, db: Session) -> str:
    experiences = db.query(Experience).filter(Experience.user_id == user.id).all()
    if not experiences:
        raise HTTPException(
            status_code=400,
            detail="No experience entries found. Add at least one via /api/profile/experiences before generating a letter."
        )

    parts = [f"Candidate: {user.username}"]
    for exp in experiences:
        entry = f"- {exp.title}" + (f" at {exp.company_name}" if exp.company_name else "") + f": {exp.description}"
        if exp.skills:
            entry += f" (Skills: {exp.skills})"
        parts.append(entry)

    return "\n".join(parts)

# Asks Gemini to pull the job title and company name out of a raw job posting
def extract_job_info(job_description: str) -> JobInfo:
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=f"""Extract the job title and companu name from this job posting.
        If either isn't explicitly staed, make you best reasonable guess or use "Unkonwn".
        
        JOB POSTING:
        {job_description}
        """,
        config={
            "response_mime_type": "application/json",
            "response_schema": JobInfo,
        }
    )
    return JobInfo.model_validate_json(response.text)

# Asks Gemini to write the actual cover letter text, tailored to the resume + job description
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

# FastAPI dependency that decodes the bearer token and loads the current User,
# raising 401 if the token or user is invalid
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_error = HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_error
    return user


from fpdf.enums import WrapMode, XPos, YPos

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# Renders the generated cover letter text into a formatted PDF and returns the raw bytes
def letter_to_pdf_bytes(letter_text: str) -> bytes:
    pdf = FPDF(format="Letter")
    pdf.set_margins(left=18, top=18, right=18)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.add_font("DejaVu", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
    pdf.add_font("DejaVu", "B", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
    pdf.set_font("DejaVu", size=10.5)

    paragraphs = [p.strip() for p in letter_text.split("\n\n") if p.strip()]

    for paragraph in paragraphs:
        lines = paragraph.split("\n")
        if len(lines) > 1:
            for line in lines:
                pdf.multi_cell(
                    0, 5.5, line, align="L", wrapmode=WrapMode.WORD,
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                )
        else:
            pdf.multi_cell(
                0, 5.5, paragraph, align="J", wrapmode=WrapMode.WORD,
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )
        pdf.ln(2.5)

    return bytes(pdf.output())


# Creates a new user with a bcrypt-hashed password, rejecting duplicate usernames
@app.post("/auth/register", status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(username=payload.username, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    return {"message": "User created"}

# Verifies username/password and returns a JWT access token
@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Icorrect username or password")
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
          

# Generates a new cover letter from a job description (using the current user's saved
# experience as background) and saves it to the DB
@app.post("/api/cover-letters", response_model=CoverLetterResponse, status_code=201)
def create_cover_letter(payload: JobDescriptionInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = build_resume_text(current_user, db)
    job_info = extract_job_info(payload.job_description)
    letter = generate_letter_text(resume, payload.job_description)

    entry = CoverLetterEntry(
        job_title=job_info.job_title,
        company_name=job_info.company_name,
        job_description=payload.job_description,
        generated_letter=letter
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

# Lists all generated cover letters, newest first
@app.get("/api/cover-letters", response_model=List[CoverLetterResponse])
def list_cover_letters(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(CoverLetterEntry).order_by(CoverLetterEntry.id.desc()).all()

# Fetches a single cover letter by id, 404s if it doesn't exist
@app.get("/api/cover-letters/{letter_id}", response_model=CoverLetterResponse)
def get_cover_letter(letter_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(CoverLetterEntry).filter(CoverLetterEntry.id == letter_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    return entry

# Renders a saved cover letter as a PDF and returns it as a downloadable attachment
@app.get("/api/cover-letters/{letter_id}/pdf")
def download_cover_letter_pdf(letter_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(CoverLetterEntry).filter(CoverLetterEntry.id == letter_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Cover letter not found")

    pdf_bytes = letter_to_pdf_bytes(entry.generated_letter)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="cover_letter_{letter_id}.pdf"'}
    )

# Adds a new experience entry (title, company, description, skills) to the current user's profile
@app.post("/api/profile/experiences", response_model=ExperienceResponse, status_code=201)
def create_experience(payload: ExperienceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exp = Experience(
        user_id=current_user.id,
        title=payload.title,
        company_name=payload.company_name,
        description=payload.description,
        skills=payload.skills,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp

# Lists all experience entries belonging to the current user
@app.get("/api/profile/experiences", response_model=List[ExperienceResponse])
def list_experiences(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Experience).filter(Experience.user_id == current_user.id).all()

# Overwrites an existing experience entry owned by the current user, 404s if not found/not theirs
@app.put("/api/profile/experiences/{experience_id}", response_model=ExperienceResponse)
def update_experience(experience_id: int, payload: ExperienceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exp = db.query(Experience).filter(Experience.id == experience_id, Experience.user_id == current_user.id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experience not found")
    exp.title = payload.title
    exp.company_name = payload.company_name
    exp.description = payload.description
    exp.skills = payload.skills
    db.commit()
    db.refresh(exp)
    return exp

# Deletes an experience entry owned by the current user, 404s if not found/not theirs
@app.delete("/api/profile/experiences/{experience_id}", status_code=204)
def delete_experience(experience_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exp = db.query(Experience).filter(Experience.id == experience_id, Experience.user_id == current_user.id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experience not found")
    db.delete(exp)
    db.commit()


##########
#Adding school details
##########
@app.post("/api/profile/schools", response_model = SchoolResponse, status_code=201)
def add_school(payload: SchoolCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scl = School(
        user_id=current_user.id,
        school_name = payload.school_name,
        degree_type = payload.degree_type,
        skills = payload.skills,
        start_date = payload.start_date,
        end_date = payload.end_date
    )
    db.add(scl)
    db.commit()
    db.refresh(scl)
    return scl

@app.get("/api/profile/schools", response_model=List[SchoolResponse])
def list_school(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(School).filter(School.user_id == current_user.id).all()

@app.put("/api/profile/schools/{school_id}", response_model=ExperienceResponse)
def update_school(school_id: int, payload: SchoolCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scl = db.query(School).filter(School.id == school_id, School.user_id == current_user.id).first()
    if not scl:
        raise HTTPException(status_code=404, detail="School not found")
    scl.school_name = payload.school_name
    scl.degree_type = payload.degree_type
    scl.skills = payload.skills
    scl.start_date = payload.start_date
    scl.end_date = payload.end_date
    db.commit()
    db.refresh(scl)
    return scl

@app.delete("/api/profile/schools/{school_id}", status_code=204)
def delete_school(school_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scl = db.query(School).filter(School.id == school_id, School.user_id == current_user.id).first()
    if not scl:
        raise HTTPException(status_code=404, detail="School not found")
    db.delete(scl)
    db.commit







