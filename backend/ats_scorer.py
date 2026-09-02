"""
ats_scorer.py
Rule-based ATS scoring engine. No external LLM calls required — everything
here is deterministic text analysis, so it's fast, free, and offline.
"""

import re
from collections import Counter

# ---------------------------------------------------------------------------
# Static reference data
# ---------------------------------------------------------------------------

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "he", "in", "is", "it", "its", "of", "on", "that", "the", "to", "was",
    "were", "will", "with", "you", "your", "we", "our", "or", "this", "these",
    "those", "their", "they", "them", "i", "us", "not", "but", "if", "than",
    "so", "into", "about", "across", "per", "etc", "such", "can", "may",
    "must", "should", "would", "could", "have", "had", "do", "does", "did",
    "over", "up", "out", "no", "yes", "all", "any", "each", "more", "most",
    "other", "some", "own", "same", "also", "including", "based", "using",
    "work", "working", "role", "roles", "job", "team", "years", "year",
    "experience", "strong", "ability", "skills", "skill", "required",
    "requirements", "responsibilities", "preferred", "plus", "etc.",
    "looking", "candidate", "like", "environment", "well", "good",
    "excellent", "great", "who", "what", "when", "where", "why", "how",
    "new", "within", "while", "very", "environment.", "field", "related",
}

STRONG_ACTION_VERBS = {
    "achieved", "built", "created", "designed", "developed", "engineered",
    "implemented", "improved", "increased", "reduced", "launched", "led",
    "managed", "optimized", "architected", "automated", "delivered",
    "deployed", "streamlined", "spearheaded", "drove", "scaled", "shipped",
    "orchestrated", "pioneered", "resolved", "accelerated", "generated",
    "established", "authored", "integrated", "refactored", "mentored",
    "coordinated", "negotiated", "analyzed", "researched", "trained",
    "presented", "migrated", "cut", "boosted", "enhanced", "modernized",
}

WEAK_VERBS_OR_PHRASES = {
    "responsible for", "worked on", "helped with", "was involved in",
    "duties included", "in charge of", "tasked with", "assisted with",
    "participated in", "handled", "did", "was part of", "involved in",
}

RESUME_SECTION_KEYWORDS = {
    "experience": ["experience", "work experience", "employment history"],
    "education": ["education", "academic background"],
    "skills": ["skills", "technical skills", "core competencies"],
    "projects": ["projects", "personal projects", "academic projects"],
    "contact": ["email", "phone", "linkedin", "github"],
}

QUANTIFIER_PATTERN = re.compile(
    r"(\$\d|\d+%|\d+x\b|\b\d+\s?(k|m|million|billion|thousand)\b|\b\d{2,}\b)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#/-]{1,}", text.lower())
    return [w.strip(".,-/") for w in words if w.strip(".,-/")]


def extract_keywords(jd_text: str, top_n: int = 30) -> list:
    """
    Pulls the most meaningful, likely-skill-or-requirement words/phrases
    out of a job description by frequency, after removing stopwords.
    Also captures common multi-word tech terms (e.g. "machine learning").
    """
    tokens = [t for t in _tokenize(jd_text) if t not in STOPWORDS and len(t) > 2]
    freq = Counter(tokens)

    # naive bigram capture for compound skill terms
    words_seq = _tokenize(jd_text)
    bigrams = [
        f"{words_seq[i]} {words_seq[i+1]}"
        for i in range(len(words_seq) - 1)
        if words_seq[i] not in STOPWORDS and words_seq[i + 1] not in STOPWORDS
    ]
    bigram_freq = Counter(bigrams)
    common_bigrams = [b for b, c in bigram_freq.items() if c >= 2]

    ranked_unigrams = [w for w, _ in freq.most_common(top_n)]
    keywords = list(dict.fromkeys(common_bigrams[:10] + ranked_unigrams))
    return keywords[:top_n]


def find_matched_and_missing(keywords: list, resume_text: str):
    resume_lower = resume_text.lower()
    matched, missing = [], []
    for kw in keywords:
        if kw in resume_lower:
            matched.append(kw)
        else:
            missing.append(kw)
    return matched, missing


def check_sections(resume_text: str) -> dict:
    resume_lower = resume_text.lower()
    found = {}
    for section, variants in RESUME_SECTION_KEYWORDS.items():
        found[section] = any(v in resume_lower for v in variants)
    return found


def analyze_bullets(resume_text: str):
    """
    Splits the resume into line-level "bullets" and flags ones that use
    weak phrasing or lack any quantified impact.
    """
    lines = [l.strip("-•* \t") for l in resume_text.split("\n") if l.strip()]
    weak_bullets, strong_bullets, unquantified_bullets = [], [], []

    for line in lines:
        if len(line.split()) < 4:
            continue  # too short to be a real bullet (likely a header/label)

        lower_line = line.lower()
        has_weak_phrase = any(phrase in lower_line for phrase in WEAK_VERBS_OR_PHRASES)
        starts_with_strong_verb = any(
            lower_line.startswith(verb) for verb in STRONG_ACTION_VERBS
        )
        has_number = bool(QUANTIFIER_PATTERN.search(line))

        if has_weak_phrase:
            weak_bullets.append(line)
        elif starts_with_strong_verb:
            strong_bullets.append(line)
            if not has_number:
                unquantified_bullets.append(line)

    return {
        "weak_bullets": weak_bullets[:8],
        "strong_bullets": strong_bullets[:8],
        "unquantified_bullets": unquantified_bullets[:8],
    }


def reframe_suggestion(bullet: str) -> str:
    """
    Produces a generic but concrete reframing template for a weak bullet,
    nudging toward: strong verb + what you did + measurable outcome.
    """
    cleaned = bullet
    for phrase in WEAK_VERBS_OR_PHRASES:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)

    # strip leftover auxiliary verbs/pronouns and collapse whitespace
    cleaned = re.sub(r"\b(was|were|is|are|i|the)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,-")
    cleaned = cleaned[0].upper() + cleaned[1:] if cleaned else cleaned

    return (
        f"Instead of \"{bullet}\", try leading with a strong action verb and "
        f"adding a measurable result, e.g. \"Led {cleaned.lower()}, "
        f"reducing/increasing [metric] by [X%]\"."
    )


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def score_resume(resume_text: str, jd_text: str) -> dict:
    keywords = extract_keywords(jd_text)
    matched, missing = find_matched_and_missing(keywords, resume_text)
    keyword_match_pct = (len(matched) / len(keywords) * 100) if keywords else 0

    sections = check_sections(resume_text)
    sections_found = sum(1 for v in sections.values() if v)
    format_score = (sections_found / len(sections)) * 100

    bullets = analyze_bullets(resume_text)
    total_bullets = len(bullets["weak_bullets"]) + len(bullets["strong_bullets"])
    action_verb_score = (
        (len(bullets["strong_bullets"]) / total_bullets * 100) if total_bullets else 50
    )

    quantified_count = len(bullets["strong_bullets"]) - len(bullets["unquantified_bullets"])
    quantify_score = (
        (quantified_count / len(bullets["strong_bullets"]) * 100)
        if bullets["strong_bullets"] else 30
    )

    word_count = len(resume_text.split())
    length_penalty = 0
    if word_count < 150:
        length_penalty = 15
    elif word_count > 1200:
        length_penalty = 10

    overall_score = round(
        keyword_match_pct * 0.45
        + format_score * 0.20
        + action_verb_score * 0.20
        + quantify_score * 0.15
        - length_penalty
    )
    overall_score = max(0, min(100, overall_score))

    strengths, weaknesses, suggestions = [], [], []

    if matched:
        strengths.append(
            f"Resume already includes {len(matched)} of {len(keywords)} key terms "
            f"from the job description, including: {', '.join(matched[:8])}."
        )
    if bullets["strong_bullets"]:
        strengths.append(
            f"{len(bullets['strong_bullets'])} bullet(s) open with strong action verbs "
            f"(e.g. built, led, optimized) — good for both ATS parsing and readability."
        )
    if sections_found >= 4:
        strengths.append("Resume contains all standard ATS-friendly sections (experience, education, skills, contact info).")
    if quantified_count > 0:
        strengths.append(f"{quantified_count} bullet(s) include measurable, quantified impact.")

    if missing:
        weaknesses.append(
            f"Missing {len(missing)} keyword(s) that appear in the job description: "
            f"{', '.join(missing[:10])}."
        )
    if bullets["weak_bullets"]:
        weaknesses.append(
            f"{len(bullets['weak_bullets'])} bullet(s) use weak/passive phrasing "
            f"(e.g. 'responsible for', 'worked on') instead of strong action verbs."
        )
    if bullets["unquantified_bullets"]:
        weaknesses.append(
            f"{len(bullets['unquantified_bullets'])} bullet(s) describe work but include no numbers, "
            f"percentages, or measurable outcomes."
        )
    missing_sections = [s for s, present in sections.items() if not present]
    if missing_sections:
        weaknesses.append(f"Resume may be missing a clearly labeled section for: {', '.join(missing_sections)}.")
    if length_penalty:
        weaknesses.append(
            "Resume length looks off for ATS parsing — "
            + ("too short, may look thin on content." if word_count < 150 else "too long, may get truncated or de-prioritized by some ATS parsers.")
        )

    if missing:
        suggestions.append(
            f"Work these missing keywords into your resume naturally where true: {', '.join(missing[:10])}."
        )
    for bullet in bullets["weak_bullets"][:5]:
        suggestions.append(reframe_suggestion(bullet))
    for bullet in bullets["unquantified_bullets"][:5]:
        suggestions.append(
            f"Add a number to this bullet if possible: \"{bullet}\" — "
            f"e.g. team size, % improvement, time saved, or scale (users/records/requests)."
        )
    if missing_sections:
        suggestions.append(
            f"Add a clearly labeled section for: {', '.join(missing_sections)} so ATS parsers can find it."
        )

    if not suggestions:
        suggestions.append("Resume already aligns well with the job description — consider minor tailoring per application.")

    return {
        "overall_score": overall_score,
        "sub_scores": {
            "keyword_match": round(keyword_match_pct),
            "formatting": round(format_score),
            "action_verbs": round(action_verb_score),
            "quantification": round(quantify_score),
        },
        "matched_keywords": matched,
        "missing_keywords": missing,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        # Exposed so main.py can optionally hand these to Gemini for deeper
        # analysis + rewriting. Not part of the "public" scoring contract.
        "_weak_bullets": bullets["weak_bullets"],
        "_unquantified_bullets": bullets["unquantified_bullets"],
    }
