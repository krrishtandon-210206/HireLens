"""
gemini_analyzer.py
Uses the Gemini API to do two things the rule-based scorer can't:
  1. Analyze WHY specific bullet points are weak (beyond just phrase-matching).
  2. Rewrite those weak bullets into strong, quantified, ATS-friendly versions.

The rule-based scorer (ats_scorer.py) still does the fast, deterministic
work of finding candidate weak/unquantified bullets and computing the score.
This module only handles the natural-language analysis + rewriting step,
and is skipped gracefully if no API key is configured.
"""

import json
import os

from google import genai
from google.genai import types

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "bullet_feedback": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original": {"type": "string"},
                    "issue": {
                        "type": "string",
                        "description": "One short sentence on specifically why this bullet is weak.",
                    },
                    "rewrite": {
                        "type": "string",
                        "description": "A rewritten version: strong action verb + specific work + plausible quantified impact placeholder if no real number is given.",
                    },
                },
                "required": ["original", "issue", "rewrite"],
            },
        },
        "overall_feedback": {
            "type": "string",
            "description": "2-3 sentences of overall feedback on the resume's weak points relative to the job description.",
        },
    },
    "required": ["bullet_feedback", "overall_feedback"],
}


def is_configured() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def analyze_and_rewrite(weak_bullets: list, unquantified_bullets: list, job_description: str) -> dict:
    """
    Sends weak/unquantified bullets to Gemini for analysis + rewriting.
    Returns a dict matching RESPONSE_SCHEMA, or raises on failure —
    callers should catch exceptions and fall back to rule-based suggestions.
    """
    bullets_to_review = list(dict.fromkeys(weak_bullets + unquantified_bullets))
    if not bullets_to_review:
        return {"bullet_feedback": [], "overall_feedback": ""}

    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options=types.HttpOptions(timeout=20_000),  # 20s, in ms — fail fast rather than hang the request
    )

    prompt = f"""You are an expert resume reviewer helping a candidate tailor their resume
to a specific job description.

Job description:
\"\"\"{job_description}\"\"\"

Here are resume bullet points that a rule-based scan flagged as weak
(passive phrasing, vague, or missing quantified impact):

{chr(10).join(f"- {b}" for b in bullets_to_review)}

For each bullet, explain briefly why it's weak relative to the job description,
then rewrite it starting with a strong action verb, keeping it truthful to the
original content, and adding a quantified impact placeholder like [X%] or [Y hours]
if no real number was given (never invent a specific fake number).
Also give 2-3 sentences of overall feedback on these weak points relative to the job description."""

    response = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            temperature=0.3,
        ),
    )

    return json.loads(response.text)
