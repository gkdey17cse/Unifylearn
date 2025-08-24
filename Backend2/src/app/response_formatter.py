def unifyResponse(provider, raw):
    return {
        "title": raw.get("Title") or raw.get("Course Title"),
        "url": raw.get("URL") or raw.get("Course URL"),
        "description": raw.get("Short Intro") or raw.get("Course Short Intro"),
        "category": raw.get("Category"),
        "subCategory": raw.get("Sub-Category"),
        "provider": provider.capitalize(),
        "skills": raw.get("Skills", "").split(",") if raw.get("Skills") else None,
        "language": raw.get("Language"),
        "duration": raw.get("Duration") or raw.get("Weekly study"),
        "rating": parseRating(raw.get("Rating")),
        "viewers": parseViewers(raw.get("Number of viewers")),
    }


def parseRating(rating):
    if not rating:
        return None
    try:
        return float(rating.replace("stars", "").strip())
    except:
        return None


def parseViewers(viewers):
    if not viewers:
        return None
    try:
        return int(viewers.replace(",", "").strip())
    except:
        return None
