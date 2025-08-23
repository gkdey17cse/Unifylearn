# src/app/services/adapters.py
# canonical document Builder - provides a consistent JSON shape the front-end (or caller) expects.
from typing import Dict, Any
from app.utils.text_utils import parse_rating_from_string, parse_skills_from_string


def normalize_doc(provider: str, raw_doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert provider-specific doc to canonical model:
      { title, url, platform, skills:[], rating: float|null, durationText, snippet, raw }
    """
    # title heuristics
    title = (
        raw_doc.get("Title")
        or raw_doc.get("CourseTitle")
        or raw_doc.get("Course Title")
        or raw_doc.get("title")
    )
    url = (
        raw_doc.get("URL")
        or raw_doc.get("Course URL")
        or raw_doc.get("CourseURL")
        or raw_doc.get("url")
    )
    # skills extraction
    skills = []
    if raw_doc.get("Skills"):
        skills = parse_skills_from_string(raw_doc.get("Skills"))
    elif raw_doc.get("What you learn"):
        skills = parse_skills_from_string(raw_doc.get("What you learn"))
    # rating
    rating_raw = raw_doc.get("Rating") or raw_doc.get("rating")
    rating = parse_rating_from_string(rating_raw)
    # snippet from short intro fields
    snippet = (
        raw_doc.get("Short Intro")
        or raw_doc.get("Course Short Intro")
        or raw_doc.get("ShortIntro")
        or ""
    )
    # durationText
    durationText = raw_doc.get("Duration") or raw_doc.get("duration") or ""
    return {
        "title": title,
        "url": url,
        "platform": provider,
        "skills": skills,
        "rating": rating,
        "durationText": durationText,
        "snippet": snippet,
        "raw": raw_doc,
    }
