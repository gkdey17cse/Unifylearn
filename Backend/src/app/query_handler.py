# src/app/query_handler.py - COMPLETE VERSION
import os
import json
from datetime import datetime
from bson import json_util
from src.app.query_generator.llm_query_builder import generate_queries
from src.app.query_executor.provider_executor import execute_provider_query
from src.app.query_executor.aggregation_executor import (
    execute_aggregation_pipeline,
    execute_cross_platform_aggregation,
)
from src.app.response_formatter import unifyResponse
from src.app.results.saver import save_results
from src.app.utils.logger import logger
from src.app.relevance_scorer import relevance_scorer


# SAVE FUNCTIONS
def save_generated_queries(generated_queries, user_query, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    queries_path = os.path.join(output_dir, "generated_queries.json")

    queries_data = {
        "user_query": user_query,
        "generated_queries": generated_queries,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(queries_path, "w", encoding="utf-8") as fh:
        json.dump(
            queries_data, fh, default=json_util.default, ensure_ascii=False, indent=2
        )

    return queries_path


def save_raw_execution_results(execution_results, user_query, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    raw_results_path = os.path.join(output_dir, "raw_execution_results.json")

    raw_results_data = {
        "user_query": user_query,
        "execution_results": execution_results,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(raw_results_path, "w", encoding="utf-8") as fh:
        json.dump(
            raw_results_data,
            fh,
            default=json_util.default,
            ensure_ascii=False,
            indent=2,
        )

    return raw_results_path


def save_raw_documents(raw_documents_by_provider, user_query, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    raw_docs_path = os.path.join(output_dir, "raw_documents.json")

    raw_docs_data = {
        "user_query": user_query,
        "raw_documents": raw_documents_by_provider,
        "total_raw_documents": sum(
            len(docs) for docs in raw_documents_by_provider.values()
        ),
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(raw_docs_path, "w", encoding="utf-8") as fh:
        json.dump(
            raw_docs_data, fh, default=json_util.default, ensure_ascii=False, indent=2
        )

    return raw_docs_path


def save_enriched_courses(all_results, output_dir):
    enriched_courses = []

    for result in all_results:
        enriched_course = {
            **result["unified_data"],
            "original_provider_id": result["original_data"].get("_id"),
            "source_provider": result["provider"],
        }
        enriched_courses.append(enriched_course)

    os.makedirs(output_dir, exist_ok=True)
    enriched_path = os.path.join(output_dir, "polished_results.json")

    with open(enriched_path, "w", encoding="utf-8") as fh:
        json.dump(
            enriched_courses,
            fh,
            default=json_util.default,
            ensure_ascii=False,
            indent=2,
        )

    return enriched_path


# DEBUG FUNCTIONS
def debug_relevance_probabilities(ranked_courses, provider_name, top_n=20):
    """Enhanced debug function to show relevance probabilities with detailed breakdown"""
    logger.info(
        f"🎯 DETAILED RELEVANCE ANALYSIS FOR {provider_name.upper()} (Top {top_n}):"
    )
    logger.info("=" * 100)

    for i, (course, probability, relevance_score, field_scores) in enumerate(
        ranked_courses[:top_n]
    ):
        title = course.get("Title", "Unknown Title")[:70]
        category = course.get("Category", "Unknown")

        # Format field scores for display
        field_score_str = " | ".join([f"{k}: {v:.2f}" for k, v in field_scores.items()])

        logger.info(
            f"{i+1:2d}. Prob: {probability:.4f} | Overall Score: {relevance_score:.4f}"
        )
        logger.info(f"    Title: {title}")
        logger.info(f"    Category: {category}")
        logger.info(f"    Field Scores: {field_score_str}")
        logger.info("-" * 100)


def create_relevance_summary(all_results, user_query):
    """Create a comprehensive relevance summary report"""
    if not all_results:
        return

    logger.info("📊 RELEVANCE SCORING SUMMARY REPORT")
    logger.info("=" * 120)
    logger.info(f"User Query: '{user_query}'")
    logger.info(f"Total Courses Processed: {len(all_results)}")

    # Calculate statistics
    probabilities = [result.get("relevance_probability", 0) for result in all_results]
    scores = [result.get("relevance_score", 0) for result in all_results]

    if probabilities:
        logger.info(
            f"Probability Range: {min(probabilities):.4f} - {max(probabilities):.4f}"
        )
        logger.info(f"Average Probability: {sum(probabilities)/len(probabilities):.4f}")
        logger.info(f"Total Probability Sum: {sum(probabilities):.4f}")

    if scores:
        logger.info(f"Score Range: {min(scores):.4f} - {max(scores):.4f}")
        logger.info(f"Average Score: {sum(scores)/len(scores):.4f}")

    # Show distribution
    prob_ranges = [(0, 0.001), (0.001, 0.01), (0.01, 0.1), (0.1, 1.0)]
    for low, high in prob_ranges:
        count = len([p for p in probabilities if low <= p < high])
        percentage = (count / len(probabilities)) * 100
        logger.info(
            f"Probability {low:.3f}-{high:.3f}: {count} courses ({percentage:.1f}%)"
        )

    logger.info("=" * 120)


# PROCESSING FUNCTIONS
def process_aggregation_query(generated_queries, user_query):
    all_results = []
    execution_results = {}
    raw_documents_by_provider = {}

    query_type = generated_queries.get("query_type", "SPJ")
    aggregation_strategy = generated_queries.get(
        "aggregation_strategy", "provider_level"
    )

    logger.aggregation(
        f"Processing {query_type} query with {aggregation_strategy} strategy"
    )

    if aggregation_strategy == "cross_platform":
        logger.aggregation("Executing cross-platform aggregation")
        combined_results, provider_results = execute_cross_platform_aggregation(
            generated_queries, user_query
        )

        execution_results.update(provider_results)

        # Apply relevance scoring before processing
        if combined_results:
            logger.info("🎯 Applying relevance scoring to cross-platform results")
            ranked_courses = relevance_scorer.rank_courses_by_relevance(
                combined_results, user_query
            )

            # DEBUG: Show probabilities
            debug_relevance_probabilities(ranked_courses, "cross_platform")

            for course, probability, relevance_score, field_scores in ranked_courses:
                provider = course.get("_provider", "unknown")
                unified_data = unifyResponse(
                    provider, course, probability, relevance_score
                )

                all_results.append(
                    {
                        "provider": provider,
                        "original_data": course,
                        "unified_data": unified_data,
                        "enrichment_applied": True,
                        "relevance_probability": probability,
                        "relevance_score": relevance_score,
                    }
                )

                if provider not in raw_documents_by_provider:
                    raw_documents_by_provider[provider] = []
                raw_documents_by_provider[provider].append(course)

    else:
        logger.aggregation("Executing provider-level aggregation")
        for provider, query in generated_queries.get("providers", {}).items():
            logger.info(f"Processing {provider}")

            # Check if this is an aggregation pipeline (list) or find query (dict)
            if isinstance(query, list):
                sanitized_docs, result_info = execute_aggregation_pipeline(
                    provider, query, user_query
                )
            else:
                sanitized_docs, result_info = execute_provider_query(
                    provider, query, user_query
                )

            execution_results[provider] = result_info
            raw_documents_by_provider[provider] = sanitized_docs or []

            # Apply relevance scoring before processing
            if sanitized_docs:
                logger.info(
                    f"🎯 Applying relevance scoring to {len(sanitized_docs)} documents from {provider}"
                )
                ranked_courses = relevance_scorer.rank_courses_by_relevance(
                    sanitized_docs, user_query
                )

                # DEBUG: Show probabilities for this provider
                debug_relevance_probabilities(ranked_courses, provider)

                for (
                    course,
                    probability,
                    relevance_score,
                    field_scores,
                ) in ranked_courses:
                    unified_data = unifyResponse(
                        provider.lower(), course, probability, relevance_score
                    )

                    all_results.append(
                        {
                            "provider": provider.lower(),
                            "original_data": course,
                            "unified_data": unified_data,
                            "enrichment_applied": True,
                            "relevance_probability": probability,
                            "relevance_score": relevance_score,
                        }
                    )

    return all_results, execution_results, raw_documents_by_provider


def processUserQuery(userQuery):
    try:
        # STEP 1: Generate queries
        logger.info("🧠 STEP 1: Generating queries with LLM...")
        generated_queries = generate_queries(userQuery)

        # DEBUG: Show the generated queries
        logger.info("🔍 GENERATED QUERIES DEBUG:")
        logger.info(f"Query Type: {generated_queries.get('query_type', 'SPJ')}")
        logger.info(f"Expanded Terms: {generated_queries.get('expanded_terms', [])}")
        logger.info(f"Thought Process: {generated_queries.get('thought_process', '')}")

        for provider, query in generated_queries.get("providers", {}).items():
            logger.info(f"Provider {provider}: {json.dumps(query, indent=2)}")

        all_results = []
        execution_results = {}
        raw_documents_by_provider = {}

        query_type = generated_queries.get("query_type", "SPJ")
        debug_info = {
            "user_query": userQuery,
            "llm_generated_queries": generated_queries,
            "query_type": query_type,
            "execution_results": execution_results,
        }

        # STEP 2: Execute queries based on type
        if query_type == "AGGREGATE":
            all_results, execution_results, raw_documents_by_provider = (
                process_aggregation_query(generated_queries, userQuery)
            )
        else:
            # SPJ query processing
            logger.info("Processing as SPJ query")
            for provider, schema_field_query in generated_queries.get(
                "providers", {}
            ).items():
                logger.info(f"Processing {provider}")

                sanitized_docs, result_info = execute_provider_query(
                    provider, schema_field_query, userQuery
                )
                execution_results[provider] = result_info
                debug_info["execution_results"][provider] = result_info
                raw_documents_by_provider[provider] = sanitized_docs or []

                # Apply relevance scoring before processing
                if sanitized_docs:
                    logger.info(
                        f"🎯 Applying relevance scoring to {len(sanitized_docs)} documents from {provider}"
                    )
                    ranked_courses = relevance_scorer.rank_courses_by_relevance(
                        sanitized_docs, userQuery
                    )

                    # DEBUG: Show probabilities for this provider
                    debug_relevance_probabilities(ranked_courses, provider)

                    for (
                        course,
                        probability,
                        relevance_score,
                        field_scores,
                    ) in ranked_courses:
                        unified_data = unifyResponse(
                            provider.lower(), course, probability, relevance_score
                        )

                        all_results.append(
                            {
                                "provider": provider.lower(),
                                "original_data": course,
                                "unified_data": unified_data,
                                "enrichment_applied": True,
                                "relevance_probability": probability,
                                "relevance_score": relevance_score,
                            }
                        )

        # STEP 3: Save results
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        output_dir = os.getenv("OUTPUT_DIR", "./results")
        query_output_dir = os.path.join(output_dir, ts)

        queries_path = save_generated_queries(
            generated_queries, userQuery, query_output_dir
        )
        raw_results_path = save_raw_execution_results(
            execution_results, userQuery, query_output_dir
        )
        raw_docs_path = save_raw_documents(
            raw_documents_by_provider, userQuery, query_output_dir
        )
        polished_path = save_enriched_courses(all_results, query_output_dir)
        debug_path = save_results(userQuery, debug_info, all_results, query_output_dir)

        logger.success(f"All files saved to {query_output_dir}")
        logger.info(f"Total results: {len(all_results)}")

        # Prepare clean results for frontend - NOW SORTED BY RELEVANCE
        frontend_results = []
        for result in all_results:
            frontend_results.append(
                {
                    **result["unified_data"],
                    "source_provider": result["provider"],
                    "original_provider_id": result["original_data"].get("_id"),
                    "enrichment_applied": result.get("enrichment_applied", False),
                    "relevance_probability": result.get("relevance_probability", 0),
                    "relevance_score": result.get("relevance_score", 0),
                }
            )

        # Sort frontend results by relevance probability (descending)
        frontend_results.sort(
            key=lambda x: x.get("relevance_probability", 0), reverse=True
        )

        # FINAL DEBUG: Show comprehensive summary
        logger.info("🏆 FINAL RANKED RESULTS (Top 15):")
        logger.info("=" * 120)
        for i, result in enumerate(frontend_results[:15]):
            logger.info(
                f"{i+1:2d}. Prob: {result.get('relevance_probability', 0):.4f} | "
                f"Score: {result.get('relevance_score', 0):.4f} | "
                f"Provider: {result.get('source_provider', 'Unknown')} | "
                f"Title: {result.get('title', 'Unknown')[:60]}"
            )

        # Create comprehensive summary
        create_relevance_summary(frontend_results, userQuery)

        return {
            "query": userQuery,
            "results": frontend_results,
            "total_results": len(frontend_results),
            "debug": debug_info,
            "output_directory": query_output_dir,
        }

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"query": userQuery, "results": [], "total_results": 0, "error": str(e)}
