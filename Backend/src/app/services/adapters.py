# src/app/services/adapters.py
from typing import Dict, Any


def _first(*vals):
    for v in vals:
        if v is not None and v != "":
            return v
    return None


def normalize_doc(provider: str, doc: Dict[str, Any]) -> Dict[str, Any]:
    p = (provider or "").lower()

    # Title + URL variants
    title = _first(doc.get("Title"), doc.get("Course Title"), doc.get("CourseTitle"))
    url = _first(doc.get("URL"), doc.get("Course URL"))

    # Intro variants
    short_intro = _first(doc.get("Short Intro"), doc.get("Course Short Intro"))

    # Level/Difficulty variants
    level = _first(doc.get("Level"), doc.get("Difficulty"), doc.get("Course Type"))

    # Skills / learning outcomes
    skills = _first(doc.get("Skills"), doc.get("What you learn"))

    # Category
    category = doc.get("Category")
    subcat = doc.get("Sub-Category")

    # Audience/showcase
    rating = doc.get("Rating")
    viewers = doc.get("Number of viewers")
    duration = doc.get("Duration") or doc.get("Weekly study")
    site = doc.get("Site")

    return {
        "provider": p,  # coursera | futurelearn | simplilearn | udacity
        "title": title,
        "url": url,
        "short_intro": short_intro,
        "category": category,
        "sub_category": subcat,
        "level": level,
        "skills_or_outcomes": skills,
        "rating": rating,
        "num_viewers": viewers,
        "duration": duration,
        "site": site,
        # raw keeps the original doc if you need to inspect exact fields later
        "_raw": doc,
    }
