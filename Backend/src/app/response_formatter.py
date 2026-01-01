# src/app/response_formatter.py - COMPLETE FIXED VERSION
from src.app.data_enrichment.uniform_formatter import format_to_universal_schema
from src.app.utils.logger import logger


def unifyResponse(provider, raw, relevance_probability=None, relevance_score=None):
    """
    Convert raw course data to universal schema format with LLM enrichment.
    """
    try:
        enriched_data = format_to_universal_schema(raw, provider)

        # Add relevance information if provided
        if relevance_probability is not None:
            enriched_data["relevance_probability"] = relevance_probability
        if relevance_score is not None:
            enriched_data["relevance_score"] = relevance_score

        return enriched_data
    except Exception as e:
        logger.error(f"Error unifying response for {provider}: {e}")
        # Return basic formatted data even if enrichment fails
        fallback_data = {
            "title": raw.get("Title", ""),
            "url": raw.get("URL", ""),
            "description": raw.get("Short Intro", ""),
            "provider": provider.capitalize(),
            "enrichment_applied": False,
        }

        # Add relevance information to fallback data too
        if relevance_probability is not None:
            fallback_data["relevance_probability"] = relevance_probability
        if relevance_score is not None:
            fallback_data["relevance_score"] = relevance_score

        return fallback_data
