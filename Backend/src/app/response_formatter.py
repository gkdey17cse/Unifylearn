from src.app.data_enrichment.uniform_formatter import format_to_universal_schema


def unifyResponse(provider, raw):
    """
    Convert raw course data to universal schema format with LLM enrichment.
    """
    return format_to_universal_schema(raw, provider)


# Keep the old functions for backward compatibility
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
