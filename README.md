# ATS Resume Analyzer

> Analyze your resume against a job description, get an ATS compatibility score, identify strengths and weaknesses, and receive actionable suggestions to improve your resume.

🌐 **Live Demo:** https://hire-lens-xi-nine.vercel.app/

---

## 📌 Overview

ATS Resume Analyzer is a lightweight resume analysis tool that evaluates how well a resume matches a specific job description.

Instead of relying entirely on expensive AI APIs, the core analysis uses a **rule-based scoring engine** that checks keywords, resume structure, action verbs, and quantified achievements.

The application can optionally use **Google Gemini** to provide more detailed explanations and rewrite weak resume bullet points.

### What it helps you answer

- How well does my resume match this job?
- Which skills from the job description are missing?
- What are the strongest parts of my resume?
- What weaknesses could reduce my ATS score?
- Which bullet points should I rewrite?
- How can I make my achievements more measurable?

---

## 🚀 Live Demo

Try the application:

**https://hire-lens-xi-nine.vercel.app/**

Upload a resume, paste a job description, and receive an analysis within seconds.

---

## ✨ Features

### 📊 ATS Compatibility Score

Generates an overall score from **0–100** based on multiple resume factors.

### 🔑 Keyword Matching

Extracts relevant skills and keywords from the job description and compares them against the resume.

Shows:

- Matched keywords
- Missing keywords
- Keyword match percentage

### 📄 Resume Structure Analysis

Checks for commonly expected resume sections such as:

- Education
- Experience
- Projects
- Skills
- Certifications
- Contact information

### 💪 Strength Analysis

Identifies positive aspects of the resume, such as:

- Strong keyword coverage
- Good use of action verbs
- Quantified achievements
- Relevant technical skills
- Proper resume structure

### ⚠️ Weakness Detection

Detects issues such as:

- Missing job-specific keywords
- Weak action verbs
- Generic descriptions
- Unquantified achievements
- Missing resume sections

### ✍️ Resume Rewriting Suggestions

Provides concrete suggestions for improving weak bullet points.

For example:

**Before**

> Worked on a web application using React.

**Suggested**

> Developed a React-based web application that improved [metric] by [X%] and reduced [process/time] by [Y%].

The system encourages measurable impact rather than simply listing responsibilities.

### 🤖 Optional Gemini Analysis

If a Gemini API key is configured, Gemini analyzes weak resume bullets and provides:

- Explanation of the problem
- Job-specific reasoning
- Improved bullet point
- Quantified-impact placeholders

If Gemini is unavailable, the application automatically falls back to the built-in rule-based suggestions.

---

## 🧮 Scoring System

The ATS score is calculated using four major components:

| Category | Weight |
|---|---:|
| 🔑 Keyword Match | 45% |
| 📄 Formatting & Sections | 20% |
| ⚡ Action Verbs | 20% |
| 📈 Quantified Impact | 15% |
| **Total** | **100%** |

### Example

```text
Keyword Match       72
Formatting          90
Action Verbs        80
Quantification      60

Overall ATS Score   76
