# src/app/utils/text_utils.py
# reusable parsers for rating and skills; also a small fallback relevance score used when ratings are missing.
import re
from typing import List

def parse_rating_from_string(s):
    """Try to extract a number from rating strings like '4.9stars' or '4.7'."""
    if not s:
        return None
    try:
        m = re.search(r"(\d+(\.\d+)?)", str(s))
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return None

def parse_skills_from_string(s):
    """Split comma/separator-separated skills into list. Safe for None."""
    if not s:
        return []
    t = str(s)
    # remove 'Subtitles:' noise or stray labels
    t = re.sub(r"Subtitles?:", "", t, flags=re.I)
    # Normalize separators
    t = t.replace(" / ", ",").replace("/", ",").replace(";", ",")
    parts = [p.strip() for p in t.split(",") if p.strip()]
    # dedupe while preserving order
    seen = set()
    out = []
    for p in parts:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out

def string_relevance_score(text: str, topic: str) -> int:
    """
    Very small relevance heuristic: count topic tokens in text.
    Lowercase, simple substring counting. Returns integer score.
    """
    if not text or not topic:
        return 0
    t = text.lower()
    tk = topic.lower()
    return t.count(tk)
