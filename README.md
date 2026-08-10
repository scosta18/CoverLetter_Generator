# Cover Letter Generator

A FastAPI backend + React frontend that generates tailored cover letters.
You give it a job description, it reads your resume, sends both to Gemini,
and hands back a cover letter — plus a PDF if you want one to actually send.

## How it works

1. You register / log in and get a JWT.
2. You paste a job description into the frontend (or POST it to
   `/api/cover-letters` directly).
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

**Backend**
- FastAPI + SQLAlchemy + SQLite
- Google Gemini (`google-genai`, model: `gemini-flash-latest`) for extraction + generation
- JWT auth (python-jose) with bcrypt password hashing (passlib)
- fpdf2 for PDF export

**Frontend**
- React 19 + Vite
- Plain `fetch` calls to the backend API (no extra HTTP/state libraries)

## Setup

### Backend

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

Docs are at `http://127.0.0.1:8000/docs` — handy for trying endpoints without
the frontend.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server talks to the backend at `http://127.0.0.1:8000` (hardcoded in
`frontend/src/App.jsx` — update that if your backend runs elsewhere). Make
sure the backend is running first.

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

- The resume is currently read from a fixed file path rather than uploaded
  per-request/per-user — fine for one person's use, won't scale to multiple
  users as-is.
- The frontend's API base URL is hardcoded rather than pulled from an env var.
- `cover_letters.db` gets created automatically on first run; it's not meant
  to be committed.
