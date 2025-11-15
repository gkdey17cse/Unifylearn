# src/app/response_formatter.py
from src.app.data_enrichment.uniform_formatter import format_to_universal_schema
from src.app.utils.logger import logger


def unifyResponse(provider, raw):
    """
    Convert raw course data to universal schema format with LLM enrichment.
    """
    try:
        enriched_data = format_to_universal_schema(raw, provider)
        return enriched_data
    except Exception as e:
        logger.error(f"Error unifying response for {provider}: {e}")
        # Return basic formatted data even if enrichment fails
        return {
            "title": raw.get("Title", ""),
            "url": raw.get("URL", ""),
            "description": raw.get("Short Intro", ""),
            "provider": provider.capitalize(),
            "enrichment_applied": False,
        }