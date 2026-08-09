# Cover Letter Generator

A small FastAPI backend that generates tailored cover letters. You give it a
job description, it reads your resume, sends both to Gemini, and hands back
a cover letter — plus a PDF if you want one to actually send.

Right now this is backend-only (no frontend yet). Everything is driven
through the API / Swagger docs.

## How it works

1. You register / log in and get a JWT.
2. You POST a job description to `/api/cover-letters`.
3. The backend:
   - reads your resume from `backend/testsubjects/resume.txt`
   - asks Gemini to pull the job title and company name out of the job description
   - asks Gemini to write the actual letter, tailored to that job + your background
   - saves the result (job title, company, description, generated letter) to SQLite
4. You can list past letters, fetch one by id, or download it as a formatted PDF.

The prompt is written to avoid inventing experience or contact details that
aren't in your resume — if something's missing (name, email, etc.) it falls
back to `[Your Name]`-style placeholders instead of making it up.

## Stack

- FastAPI + SQLAlchemy + SQLite
- Google Gemini (`google-genai`, model: `gemini-flash-latest`) for extraction + generation
- JWT auth (python-jose) with bcrypt password hashing (passlib)
- fpdf2 for PDF export

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # or `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:

```
GEMINI_API_KEY=your-gemini-api-key
JWT_SECRET_KEY=some-long-random-string
```

Drop your resume as plain text at `backend/testsubjects/resume.txt` (there's
already a sample one in that folder — replace it with your own).

Run the API:

```bash
uvicorn app:app --reload
```

Docs are at `http://127.0.0.1:8000/docs` — easiest way to try everything out
without a frontend.

## API

| Method | Route | Auth | What it does |
|---|---|---|---|
| POST | `/auth/register` | – | create a user |
| POST | `/auth/login` | – | log in, get a bearer token |
| POST | `/api/cover-letters` | ✅ | generate a new cover letter from a job description |
| GET | `/api/cover-letters` | ✅ | list your generated cover letters |
| GET | `/api/cover-letters/{id}` | ✅ | fetch one |
| GET | `/api/cover-letters/{id}/pdf` | ✅ | download it as a PDF |

Auth is a standard OAuth2 password flow — log in, take the `access_token`,
send it as `Authorization: Bearer <token>` on everything else.

## Notes / TODO

- No frontend yet — this is just the API for now.
- The resume is currently read from a fixed file path rather than uploaded
  per-request/per-user — fine for one person's use, won't scale to multiple
  users as-is.
- `cover_letters.db` gets created automatically on first run; it's not meant
  to be committed.
