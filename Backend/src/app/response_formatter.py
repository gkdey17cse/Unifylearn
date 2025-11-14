# src/app/response_formatter.py
from src.app.data_enrichment.uniform_formatter import format_to_universal_schema


def unifyResponse(provider, raw):
    """
    Convert raw course data to universal schema format with LLM enrichment.
    Returns enriched data with enrichment tracking.
    """
    print(f"🔄 Formatting and enriching data for provider: {provider}")
    print(f"📄 Raw document keys: {list(raw.keys())}")

    enriched_data = format_to_universal_schema(raw, provider)

    # Track if enrichment was actually applied
    if enriched_data.get("_enrichment_applied"):
        print("✅ LLM enrichment was applied")
    else:
        print("ℹ️  Using basic formatting without LLM enrichment")

    return enriched_data


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
