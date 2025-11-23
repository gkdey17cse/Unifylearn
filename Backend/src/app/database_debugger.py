# src/app/database_debugger.py - NEW FILE
import json
from src.app.db_connection import dbMap, COLLECTION_MAP, get_collection
from src.app.utils.logger import logger


def debug_database_connections():
    """Debug database connections and collections"""
    logger.info("🔍 DATABASE CONNECTION DEBUG")
    logger.info("=" * 80)

    for provider in ["coursera", "udacity", "simplilearn", "futurelearn"]:
        try:
            db = dbMap.get(provider)
            collection_name = COLLECTION_MAP.get(provider)

            if db is None:
                logger.error(f"❌ {provider.upper()}: Database not configured")
                continue

            if collection_name is None:
                logger.error(f"❌ {provider.upper()}: Collection name not configured")
                continue

            collection = db[collection_name]

            # Test connection and count documents
            count = collection.count_documents({})
            logger.info(
                f"✅ {provider.upper()}: Connected | Collection: {collection_name} | Documents: {count}"
            )

            # Show sample document structure
            if count > 0:
                sample = collection.find_one({})
                if sample:
                    logger.info(f"   Sample fields: {list(sample.keys())[:10]}...")

        except Exception as e:
            logger.error(f"❌ {provider.upper()}: Connection failed - {str(e)}")


def test_query_execution(generated_queries, user_query):
    """Test query execution for all providers"""
    logger.info("🔍 QUERY EXECUTION DEBUG")
    logger.info("=" * 80)

    from src.app.query_executor.provider_executor import execute_provider_query

    for provider, query in generated_queries.get("providers", {}).items():
        logger.info(f"Testing {provider.upper()}...")
        logger.info(f"Query: {json.dumps(query, indent=2)}")

        try:
            sanitized_docs, result_info = execute_provider_query(
                provider, query, user_query
            )

            logger.info(
                f"Results: {len(sanitized_docs) if sanitized_docs else 0} documents"
            )
            logger.info(
                f"Execution Info: {json.dumps(result_info, indent=2, default=str)}"
            )

            if sanitized_docs and len(sanitized_docs) > 0:
                logger.info(
                    f"First document title: {sanitized_docs[0].get('Title', 'No Title')}"
                )

        except Exception as e:
            logger.error(f"❌ {provider.upper()}: Query execution failed - {str(e)}")

        logger.info("-" * 60)
