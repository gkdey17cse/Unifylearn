# src/app/nlp/parser_rule_based.py
import re
from typing import Dict, Any, List

PLATFORM_WORDS = {
    "coursera": ["coursera"],
    "futurelearn": ["futurelearn", "future learn"],
    "simplilearn": ["simplilearn", "simpli learn"],
    "udacity": ["udacity"],
}
LEVEL_WORDS = {
    "beginner": r"(beginner|beginners|intro(ductory)?|basic|foundation(s)?)",
    "intermediate": r"(intermediate)",
    "advanced": r"(advanced|expert)",
}


def _find_platforms(q: str) -> List[str]:
    ql = q.lower()
    found = []
    for k, words in PLATFORM_WORDS.items():
        if any(w in ql for w in words):
            found.append(k)
    return found or None


def _find_level(q: str) -> str | None:
    ql = q.lower()
    for lvl, patt in LEVEL_WORDS.items():
        if re.search(rf"\b{patt}\b", ql):
            return lvl
    return None


def _find_limit(q: str) -> int | None:
    m = re.search(r"\btop\s+(\d+)\b", q.lower())
    if m:
        return int(m.group(1))
    m = re.search(r"\b(\d+)\s+(results|courses)\b", q.lower())
    if m:
        return int(m.group(1))
    return None


def _find_topic(q: str) -> str | None:
    """
    Heuristics:
    - grab phrase after 'in|on|about' up to 'course' or end
    - otherwise, take the noun-like token right before 'course(s)'
    - fallback: longest capitalized word (Python, SQL, Tableau)
    """
    ql = q.lower()

    # after 'in|on|about'
    m = re.search(r"(in|on|about)\s+([a-z0-9+\-# .]+?)(?=\s+course|$)", ql)
    if m:
        cand = m.group(2).strip()
        if cand and cand not in ("course", "courses"):
            return cand.title()

    # before 'course(s)'
    m = re.search(r"([a-z0-9+\-# .]+)\s+course(s)?", ql)
    if m:
        cand = m.group(1).strip()
        # trim trailing 'for <level>'
        cand = re.sub(
            r"\s+for\s+(beginners?|intermediate|advanced).*", "", cand
        ).strip()
        if cand:
            return cand.title()

    # fallback: pick a common tech word in Title case
    tokens = re.findall(r"\b[A-Z][a-zA-Z0-9+\-#]{1,}\b", q)
    if tokens:
        # choose the longest (Python, Machine Learning, etc.)
        return sorted(tokens, key=len, reverse=True)[0]

    return None


def parse_user_query(q: str) -> Dict[str, Any]:
    q = (q or "").strip()
    platforms = _find_platforms(q)
    level = _find_level(q)
    limit = _find_limit(q)
    topic = _find_topic(q)
    return {
        "raw": q,
        "platforms": platforms,  # list[str] | None
        "topic": topic,  # e.g., "Python"
        "level": level,  # beginner|intermediate|advanced|None
        "limit": limit,  # int|None
        "sort": None,
    }
