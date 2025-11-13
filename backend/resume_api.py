from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import List
import json, os, re
from typing import Dict, Any
import requests
from openai import OpenAI
from dotenv import load_dotenv
import time
from datetime import datetime
import pytz
import random

load_dotenv()

router = APIRouter(prefix="/resume", tags=["Resume"])

class Education(BaseModel):
    degree: str
    category: str
    from_year: str
    to_year: str
    location: str
    university: str

class Experience(BaseModel):
    role: str
    company: str
    from_date: str
    to_date: str
    location: str
    responsibilities: str

class Resume(BaseModel):
    name: str
    role_name: str
    email: str
    phone: str
    address: str
    linkedin: str
    profile_summary: str
    education: List[Education]
    experience: List[Experience]
    skills: str

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_URL = os.getenv("MODEL_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
RESUME_PATH = os.getenv("RESUME_PATH")
client = OpenAI()

COUNTS_DIR = "data/counts"
os.makedirs(COUNTS_DIR, exist_ok=True)

def increment_customize_count(resume_name: str):
    """Increment daily count for a given resume customization (CET timezone)."""
    try:
        # --- Use Central European Time ---
        cet = pytz.timezone("Europe/Warsaw")  # CET/CEST auto handled
        today = datetime.now(cet).strftime("%Y-%m-%d")

        count_path = os.path.join(COUNTS_DIR, f"{today}.json")

        # Load existing counts or start new
        if os.path.exists(count_path):
            with open(count_path, "r", encoding="utf-8") as f:
                counts = json.load(f)
        else:
            counts = {}

        # Normalize the name for consistent keys
        key = resume_name.strip().replace(" ", "_").lower()
        counts[key] = counts.get(key, 0) + 1

        # Save updated count
        with open(count_path, "w", encoding="utf-8") as f:
            json.dump(counts, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"⚠️ Failed to update count for {resume_name}: {e}")

def call_model(system_prompt: str, user_content: str) -> str:
    """Reusable helper using OpenAI SDK with retry logic."""
    for attempt in range(3):  # up to 3 retries
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
            return response.choices[0].message.content

        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                wait = 2 ** attempt
                print(f"⚠️ Rate limit hit. Retrying in {wait}s...")
                time.sleep(wait)
                continue
            else:
                raise e
    raise RuntimeError("Failed after 3 retries.")

@router.post("/coverletter")
def generate_cover_letter(payload: dict = Body(...)):
    """
    Generate a personalized cover letter from a resume and job description.
    """
    try:
        resume = payload.get("resume")
        job_description = payload.get("job_description", "")

        if not resume or not job_description:
            return {"error": "Missing resume or job_description"}

        # --- Build a compact structured prompt ---
        system_prompt = (
            "You are an expert career writer and HR communication specialist. "
            "Given a candidate's resume and a job description, write a concise, professional, "
            "and personalized cover letter tailored for that job.\n"
            "Rules:\n"
            "- Use a formal yet approachable tone.\n"
            "- Highlight the most relevant skills and experiences from the resume.\n"
            "- Align achievements to the key requirements of the job description.\n"
            "- Limit to 3–5 short paragraphs.\n"
            "- Do not include placeholders like [Company Name] or [Your Name] or even [Date]; fill them in using the given data.\n"
            "- Don't put any date in cover letter, and for Hiring manager's name, don't put specific name, but just mention as Hiring Manager\n"
            "- Return JSON with one key: cover_letter (as plain text)."
        )

        user_input = json.dumps(
            {
                "resume": resume,
                "job_description": job_description,
            },
            ensure_ascii=False,
        )

        # --- Call model ---
        response = json.loads(call_model(system_prompt, user_input))
        cover_letter = response.get("cover_letter", "")

        return {"cover_letter": cover_letter}

    except Exception as e:
        return {"error": str(e)}

@router.post("/customize")
def customize_resume(payload: dict = Body(...)):
    """
    Optimized resume customization with:
    1️⃣ Job info extracted once
    2️⃣ Separate API call for each experience responsibilities
    3️⃣ Summary rewrite
    4️⃣ Skills extension/reordering
    Produces same output as original, but far fewer tokens overall.
    """
    try:
        resume = payload.get("resume")
        job_description = payload.get("job_description", "")
        if not resume or not job_description:
            return {"error": "Missing resume or job_description"}

        # --- 0️⃣ Extract job insights once ---
        job_extract_prompt = (
            "Extract from this job description a concise summary of:\n"
            "- role_name (Should be simple and regular term, level should be always Senior -> role name should start from Senior and end with Engineer: Senior *** Engineer, *** should be one word -> if it's something like machine learning -> be in one word like ML) -> \n- company_name\n"
            "- list of skills (array)\n"
            "- It should be an array of one skill keyword, seperate different skills into different elements\n"
            "- A skill can be a framework, a library, strategy, cloud service, third party tool or anything technical related things\n"
            "- Add all skills even they are in nice-to-have or optional\n"
            "- Try to find as amany skills as possible\n"
            "- Sort skills by importancy, primary skills first, related skills second, and behavioral skills latest\n"
            "Return JSON with keys: role_name, company_name, skills"
        )
        job_info = json.loads(call_model(job_extract_prompt, job_description))
        job_skills = job_info.get("skills", [])
        job_role = job_info.get("role_name", "")
        job_company = job_info.get("company_name", "")

        # --- 1️⃣ Rewrite Profile Summary ---
        summary_prompt = (
            "You are a professional resume writer. "
            "Rewrite this profile summary to perfectly match the extracted job skills and role. "
            "Focus on highlighting the job-required skills first, then original strengths. "
            "Show numbers in number format -> 9 (not nine) "
            "Highlight tech stack (in bold font, A skill can be a framework, a library, strategy, cloud service, third party tool or anything technical related things) "
            "Return JSON with one key: profile_summary."
        )
        summary_input = json.dumps(
            {
                "current_summary": resume.get("profile_summary", ""),
                "job_skills": job_skills,
                "job_role": job_role,
            },
            ensure_ascii=False,
        )
        summary_result = json.loads(call_model(summary_prompt, summary_input))
        new_summary = summary_result.get("profile_summary", resume.get("profile_summary", ""))

        # --- 2️⃣ Rewrite Experience Responsibilities (separate API call per job) ---
        experiences = resume.get("experience", [])
        updated_experiences = []

        for idx, exp in enumerate(experiences):
            exp_prompt = (
                    "You are a professional resume writer. "
                    "Rewrite these responsibilities to perfectly match the extracted job skills and role. "
                    "Required job skills are : {job_skills}\n"
                    "Job role name is : {job_role}\n"
                    "Focus on highlighting the job-required skills first, then original strengths. "
                    "Express all job skills in bullet points of responsibilities.\n"
                    "Show numbers in number format -> 9 (not nine)\n"
                    "Highlight tech stack (in bold font, A skill can be a framework, a library, strategy, cloud service, third party tool or anything technical related things)\n"
                    "Add at least 3 numbers like measurements and version (add numbers in bullet points), Highlight these as well (in bold font)\n"
                    "Return JSON with one key: responsibilities (as text with newline-separated bullet points)."
                )

            exp_input = json.dumps(
                {
                    "responsibilities": exp["responsibilities"],
                    "job_skills": job_skills,
                    "job_role": job_role,
                },
                ensure_ascii=False,
            )

            try:
                exp_result = json.loads(call_model(exp_prompt, exp_input))
                # exp["responsibilities"] = exp_result.get("responsibilities", exp.get("responsibilities", ""))
                exp["responsibilities"] = exp_result.get("responsibilities", exp.get("responsibilities", ""))
            except Exception as e:
                exp["responsibilities"] = exp.get("responsibilities", "")
            updated_experiences.append(exp)

        # --- 3️⃣ Extend and Reorder Skills ---
        skills_prompt = (
            "You are a technical skill curator.\n"
            "Combine the current resume skills with all job-related skills. "
            "Required job skills are : {job_skills}\n"
            "Current skills are : {current_skills}\n"
            "Keep all original skills, add new ones from job_skills, remove duplicates, "
            "and reorder skills from job_skills to others\n"
            "Group skills into different categories, Show Group name first, and show a linebreak, and then a tab padding, after that please show skills\n"
            "Display in bold font for group names\n"
            "Add another line break between Groups\n"
            "These are group names: Programming Languages, Backend Frameworks, Frontend Frameworks, API Technologies, Serverless and Cloud Functions, Databases, DevOps, Cloud & Infrastructure, Other\n"
            "Return JSON with key: skills (as a comma-separated string)."
        )
        skills_input = json.dumps(
            {"current_skills": resume.get("skills", ""), "job_skills": job_skills},
            ensure_ascii=False,
        )
        skills_result = json.loads(call_model(skills_prompt, skills_input))
        new_skills = skills_result.get("skills", resume.get("skills", ""))

        # --- Merge and return ---
        updated_resume = resume.copy()
        updated_resume["profile_summary"] = new_summary
        updated_resume["experience"] = updated_experiences
        updated_resume["experience"][0]["role"] = job_role
        updated_resume["skills"] = new_skills
        updated_resume["role_name"] = job_role
        updated_resume["apply_company"] = job_company

        resume_name = resume.get("name", "unknown_user")
        increment_customize_count(resume_name)

        return updated_resume

    except Exception as e:
        return {"error": str(e)}
        
@router.post("/")
def save_resume(resume: Resume):
    os.makedirs(RESUME_PATH, exist_ok=True)
    filename = f"{RESUME_PATH}/resume_{resume.name.replace(' ', '_').lower()}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(resume.dict(), f, indent=2, ensure_ascii=False)
    return {"message": f"Resume saved as {filename}", "success": True}


@router.get("/{name}")
def get_resume(name: str):
    filename = f"{RESUME_PATH}/resume_{name.replace(' ', '_').lower()}.json"
    if not os.path.exists(filename):
        return {"error": "Resume not found"}
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/")
def list_resumes():
    """List available saved resumes."""
    os.makedirs(RESUME_PATH, exist_ok=True)
    files = [f for f in os.listdir(RESUME_PATH) if f.startswith("resume_") and f.endswith(".json")]
    names = [f.replace("resume_", "").replace(".json", "").replace("_", " ").title() for f in files]
    return {"resumes": names}

from fastapi.responses import StreamingResponse
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    ListFlowable, ListItem
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
import html

def markdown_to_html_bold(text: str) -> str:
    """Convert Markdown-style bold (**text**) into HTML <b>text</b> tags."""
    if not text:
        return ""
    # Replace pairs of **text** with <b>text</b>
    return re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

def apply_style_variant(style_id: int):
    """Return color, font, and layout settings based on style_id."""
    if style_id == 1:
        return dict(font="Helvetica", accent=colors.HexColor("#007bff"), line_thickness=0.6)
    elif style_id == 2:
        return dict(font="Courier", accent=colors.HexColor("#ff6600"), line_thickness=1.0)
    elif style_id == 3:
        return dict(font="Times-Roman", accent=colors.HexColor("#28a745"), line_thickness=0.8)
    elif style_id == 4:
        return dict(font="Helvetica-Oblique", accent=colors.HexColor("#6610f2"), line_thickness=0.7)
    elif style_id == 5:
        return dict(font="Times-Italic", accent=colors.HexColor("#16a085"), line_thickness=0.5)
    elif style_id == 6:
        return dict(font="Helvetica-Bold", accent=colors.HexColor("#dc3545"), line_thickness=0.9)
    else:  # style_id == 7
        return dict(font="Helvetica", accent=colors.HexColor("#17a2b8"), line_thickness=0.6)

@router.post("/pdf")
def generate_resume_pdf(resume: Resume):
    """Generate a professional resume PDF with bullet points for responsibilities."""
    style_id = random.randint(1, 7)
    style = apply_style_variant(style_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=50
    )

    # --- Styles using built-in fonts ---
    st_name = ParagraphStyle(
        "name",
        fontName=style["font"],
        fontSize=20,
        leading=24,
        spaceAfter=8,
        textColor=style["accent"]
    )
    st_title = ParagraphStyle("title", fontName="Helvetica-Oblique", fontSize=11.5, leading=14, spaceAfter=10)
    st_p = ParagraphStyle("p", fontName=style["font"], fontSize=10.5, leading=14)
    st_section = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13.5, leading=16, spaceBefore=12, spaceAfter=6, textColor=style["accent"])
    st_bullet = ParagraphStyle("bullet", fontName=style["font"], fontSize=10.5, leading=14, leftIndent=14)

    story = []

    # --- Header ---
    story.append(Paragraph(html.escape(resume.name or ""), st_name))
    story.append(Spacer(1, 4))
    story.append(Paragraph(html.escape(resume.role_name or ""), st_title))
    contact = " | ".join(
        [x for x in [resume.email, resume.phone, resume.address] if x]
    )
    if contact:
        story.append(Paragraph(html.escape(contact), st_p))
    if resume.linkedin:
        story.append(Paragraph(f"<a href='{html.escape(resume.linkedin)}'>{html.escape(resume.linkedin)}</a>", st_p))
    story.append(Spacer(1, 10))
    # story.append(HRFlowable(width="100%", color=colors.black, thickness=0.6, spaceBefore=6, spaceAfter=10))
    story.append(HRFlowable(
        width="100%",
        color=style["accent"],
        thickness=style["line_thickness"],
        spaceBefore=6,
        spaceAfter=10
    ))

    # --- Profile Summary ---
    if resume.profile_summary:
        story.append(Paragraph("Profile Summary", st_section))
        # story.append(Paragraph(html.escape(resume.profile_summary).replace("\n", "<br/>"), st_p))
        summary_text = markdown_to_html_bold(resume.profile_summary)
        summary_text = html.escape(summary_text, quote=False).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
        summary_text = summary_text.replace("\n", "<br/>")
        story.append(Paragraph(summary_text, st_p))

    # --- Education ---
    if resume.education:
        story.append(Paragraph("Education", st_section))
        for edu in resume.education:
            text = (
                f"<b>{html.escape(edu.degree)}</b> — {html.escape(edu.university)} "
                f"({html.escape(edu.from_year)}–{html.escape(edu.to_year)})"
                f"<br/>{html.escape(edu.location)}"
            )
            story.append(Paragraph(text, st_p))
            story.append(Spacer(1, 4))

    # --- Experience ---
    if resume.experience:
        story.append(Paragraph("Professional Experience", st_section))
        for exp in resume.experience:
            story.append(Paragraph(
                f"<b>{html.escape(exp.role)}</b> — {html.escape(exp.company)} "
                f"({html.escape(exp.from_date)}–{html.escape(exp.to_date)})", st_p))
            if exp.location:
                story.append(Paragraph(html.escape(exp.location), st_p))
            story.append(Spacer(1, 4))

            # --- Responsibilities with bullet points ---
            bullets = [
                b.strip("•-\u2022\t ") for b in (exp.responsibilities or "").splitlines() if b.strip()
            ]
            if bullets:
                story.append(ListFlowable(
                    # [ListItem(Paragraph(html.escape(line), st_bullet)) for line in bullets],
                    [ListItem(Paragraph(
                        html.escape(markdown_to_html_bold(line), quote=False)
                            .replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>"),
                        st_bullet
                    )) for line in bullets],
                    bulletType="bullet",
                    bulletFontName="Helvetica",
                    bulletFontSize=8.5,
                    leftIndent=10,
                    bulletIndent=0
                ))
            story.append(Spacer(1, 8))

    # --- Skills ---
    if resume.skills:
        story.append(Paragraph("Skills", st_section))
        # story.append(Paragraph(html.escape(resume.skills).replace("\n", "<br/>"), st_p))
        skills_text = markdown_to_html_bold(resume.skills)
        skills_text = html.escape(skills_text, quote=False).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
        skills_text = skills_text.replace("\n", "<br/>")
        story.append(Paragraph(skills_text, st_p))

    doc.build(story)
    buffer.seek(0)

    filename = f"{(resume.name or 'resume').replace(' ', '_')}_resume.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/counts/{date}")
def get_counts(date: str):
    """
    Return customization counts for a given date (YYYY-MM-DD).
    Always include all resumes, even those with 0 counts.
    """
    counts_dir = "data/counts"
    os.makedirs(counts_dir, exist_ok=True)
    path = os.path.join(counts_dir, f"{date}.json")

    # Load existing counts
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            counts = json.load(f)
    else:
        counts = {}

    # ✅ Get all resume names from saved resumes
    resumes_path = os.getenv("RESUME_PATH", "data/resumes")
    os.makedirs(resumes_path, exist_ok=True)
    files = [f for f in os.listdir(resumes_path) if f.startswith("resume_") and f.endswith(".json")]
    all_resumes = [
        f.replace("resume_", "").replace(".json", "").replace("_", " ").lower()
        for f in files
    ]

    # ✅ Merge counts (include 0 for missing)
    merged_counts = {}
    for name in all_resumes:
        key = name.replace(" ", "_")
        merged_counts[key] = counts.get(key, 0)

    # ✅ Also keep any extra names in counts (if resume file was deleted)
    for key, value in counts.items():
        if key not in merged_counts:
            merged_counts[key] = value

    return {
        "date": date,
        "counts": merged_counts,
        "total": sum(merged_counts.values()),
        "resumes": list(merged_counts.keys()),
    }
