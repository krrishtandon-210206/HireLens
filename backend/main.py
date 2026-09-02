"""
main.py
FastAPI entry point for the ATS Resume Analyzer.

Run locally:
    uvicorn main:app --reload --port 8000

Then open frontend/index.html in a browser (or serve it separately).
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from resume_parser import extract_text
from ats_scorer import score_resume
import gemini_analyzer

app = FastAPI(title="ATS Resume Analyzer")

# Allow the simple static frontend (opened via file:// or a dev server) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
):
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")

    file_bytes = await resume.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded resume file is empty.")

    try:
        resume_text = extract_text(resume.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract any text from the resume. If it's a scanned/image PDF, try a text-based export instead.",
        )

    result = score_resume(resume_text, job_description)
    weak_bullets = result.pop("_weak_bullets")
    unquantified_bullets = result.pop("_unquantified_bullets")

    result["ai_powered"] = False
    if gemini_analyzer.is_configured():
        try:
            gemini_result = gemini_analyzer.analyze_and_rewrite(
                weak_bullets, unquantified_bullets, job_description
            )
            if gemini_result.get("bullet_feedback"):
                result["ai_powered"] = True
                result["ai_overall_feedback"] = gemini_result.get("overall_feedback", "")
                result["ai_bullet_rewrites"] = gemini_result["bullet_feedback"]
                # Replace the template-based weak-bullet suggestions with
                # Gemini's — keep the missing-keyword / missing-section ones.
                result["suggestions"] = [
                    s for s in result["suggestions"]
                    if not s.startswith("Instead of") and not s.startswith("Add a number")
                ] + [
                    f"{item['issue']} Rewrite: \"{item['rewrite']}\""
                    for item in gemini_result["bullet_feedback"]
                ]
        except Exception as e:
            # Fall back silently to the rule-based suggestions already in `result`.
            result["ai_error"] = f"Gemini analysis unavailable, showing rule-based suggestions instead: {e}"

    return result
