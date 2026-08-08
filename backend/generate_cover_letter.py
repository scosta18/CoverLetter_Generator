import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def generate_cover_letter(resume: str, job_description: str) -> str:
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

if __name__ == "__main__":
    resume = read_file("testsubjects/resume.txt")
    job_description = read_file("testsubjects/job_description.txt")

    letter = generate_cover_letter(resume, job_description)

    with open("cover_letter.txt", "w", encoding="utf-8") as f:
        f.write(letter)

    print("Cover letter saved to cover_letter.txt\n")
    print(letter)