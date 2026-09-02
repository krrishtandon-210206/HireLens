# ATS Resume Analyzer

A simple project that scores a resume against a job description and gives
you an ATS score, strengths, weaknesses, and concrete rewrite suggestions.
No external API keys or paid services needed — the scoring is rule-based.

## File Structure

```
ats-resume-analyzer/
├── backend/
│   ├── main.py             # FastAPI app, exposes POST /analyze
│   ├── resume_parser.py    # Extracts text from .pdf / .docx / .txt
│   ├── ats_scorer.py       # Keyword matching, formatting checks, scoring logic
│   ├── gemini_analyzer.py  # Optional: Gemini-powered weak-point analysis + rewrites
│   ├── .env.example        # Copy to .env and add your Gemini API key
│   └── requirements.txt
├── frontend/
│   ├── index.html          # Upload form + results UI
│   ├── style.css
│   └── script.js           # Calls the backend API, renders results
└── README.md
```

## How it works

1. You upload a resume file and paste a job description.
2. The backend extracts plain text from the resume (PDF/DOCX/TXT).
3. It pulls likely keywords/skills out of the job description by frequency.
4. It compares those keywords against your resume, checks for standard
   resume sections, scans bullet points for weak phrasing
   ("responsible for", "worked on") vs. strong action verbs, and checks
   whether bullets include quantified results (%, $, numbers).
5. It combines these into an overall ATS score (0–100), plus a breakdown:
   - Keyword Match (45%)
   - Formatting / sections present (20%)
   - Action verb usage (20%)
   - Quantified impact (15%)
6. It returns strengths, weaknesses, and specific reframing suggestions
   for weak bullet points.
7. **If a Gemini API key is configured**, the weak/unquantified bullets
   found in step 4 are sent to Gemini, which explains *why* each one is
   weak relative to the job description and rewrites it with a strong
   verb + quantified-impact placeholder. If no key is set (or the call
   fails for any reason — bad key, no internet, rate limit), the app
   automatically falls back to the rule-based template suggestions —
   nothing breaks either way.

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Optional — enable Gemini-powered rewrites:**
1. Get a free API key at https://aistudio.google.com/apikey
2. Copy `.env.example` to `.env`: `cp .env.example .env`
3. Paste your key into `.env` as `GEMINI_API_KEY=...`

Without this step, the app still works fully — it just uses the
rule-based template suggestions instead of Gemini's rewrites.

```bash
uvicorn main:app --reload --port 8000
```

The API will be live at `http://127.0.0.1:8000`. You can check
`http://127.0.0.1:8000/health` to confirm it's running, and
`http://127.0.0.1:8000/docs` for interactive API docs.

### 2. Frontend

No build step needed — it's plain HTML/CSS/JS.

Just open `frontend/index.html` directly in your browser, or serve it:

```bash
cd frontend
python -m http.server 5500
```

Then visit `http://127.0.0.1:5500`.

> If your backend runs on a different host/port, update `API_URL` at the
> top of `frontend/script.js`.

## API

**POST** `/analyze`
Form-data fields:
- `resume` — file upload (.pdf, .docx, or .txt)
- `job_description` — string (plain text)

Returns JSON:
```json
{
  "overall_score": 72,
  "sub_scores": {
    "keyword_match": 65,
    "formatting": 80,
    "action_verbs": 75,
    "quantification": 60
  },
  "matched_keywords": ["python", "fastapi", "..."],
  "missing_keywords": ["kubernetes", "..."],
  "strengths": ["..."],
  "weaknesses": ["..."],
  "suggestions": ["..."],
  "ai_powered": true,
  "ai_overall_feedback": "2-3 sentences from Gemini on the weak points overall",
  "ai_bullet_rewrites": [
    {"original": "...", "issue": "...", "rewrite": "..."}
  ]
}
```

`ai_powered`, `ai_overall_feedback`, and `ai_bullet_rewrites` are only
present when a `GEMINI_API_KEY` is configured and the call succeeds.

## Ideas for extending this later

- Swap the rule-based keyword extraction for a proper NLP library (spaCy)
  or embeddings to catch synonyms (resume says "ML", JD says "machine learning").
- Try a different Gemini model via the `GEMINI_MODEL` env var (defaults to
  `gemini-2.5-flash`) if you want faster/cheaper or more capable output.
- Store analysis history per user with a small SQLite database.
- Support multiple job descriptions to compare one resume against several
  postings at once.
