# src/app/nlp/parser_rule_based.py
import re
from typing import Dict, Any, List

PLATFORM_KEYWORDS = {
    "coursera": ["coursera"],
    "futurelearn": ["futurelearn", "future learn", "future-learn"],
    "simplilearn": ["simplilearn", "simpli learn", "simpli-learn"],
    "udacity": ["udacity"],
}

TOP_SYNONYMS_TOP = ["top", "best", "highest rated", "highest-rated", "highest"]
TOP_SYNONYMS_WORST = ["worst", "less important", "low rated", "least", "lowest rated"]


def extract_platforms(text: str) -> List[str]:
    t = text.lower()
    found = []
    for key, variants in PLATFORM_KEYWORDS.items():
        for v in variants:
            if v in t:
                found.append(key)
                break
    return found


def extract_limit(text: str) -> int:
    # patterns like "top 5", "top 10", "5 results", "limit 5"
    m = re.search(r"top\s+(\d+)", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"limit\s+(\d+)", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s+(results|courses|items)\b", text, re.I)
    if m:
        return int(m.group(1))
    return None


def extract_sort(text: str) -> str:
    tl = text.lower()
    if any(k in tl for k in TOP_SYNONYMS_TOP):
        return "desc"
    if any(k in tl for k in TOP_SYNONYMS_WORST):
        return "asc"
    return None


def extract_topic(text: str) -> str:
    # 1) try quoted phrase
    m = re.search(r'["“](.+?)["”]', text)
    if m:
        return m.group(1).strip()
    # 2) after 'in|about|for' pick next 1-4 words phrase
    m = re.search(r"\b(?:in|about|for)\s+([A-Za-z0-9 &+/-]{3,80})", text, re.I)
    if m:
        candidate = m.group(1).strip().rstrip(".,?")
        # if candidate contains certain stopwords at end, trim
        return candidate
    # 3) fallback: pick last noun-ish phrase: last 2 words if they are alphabets
    tokens = re.findall(r"[A-Za-z0-9\+\-]+", text)
    if tokens:
        # return the longest token sequence that is > 2 letters (heuristic)
        # prefer multi-word starting from first content word (after common prefixes)
        filtered = [t for t in tokens if len(t) > 2]
        if filtered:
            # return joined last two as fallback
            return " ".join(filtered[-2:])
    return None


def parse_user_query(text: str) -> Dict[str, Any]:
    text = text.strip()
    platforms = extract_platforms(text)
    if not platforms:
        platforms = None  # meaning 'search all'
    limit = extract_limit(text)
    sort_dir = extract_sort(text)
    topic = extract_topic(text)
    return {
        "raw": text,
        "platforms": platforms,
        "topic": topic,
        "limit": limit,
        "sort": sort_dir,
    }
