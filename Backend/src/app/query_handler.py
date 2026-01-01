# src/app/query_handler.py - COMPLETE FIXED VERSION
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
    """Enhanced debug function to show relevance probabilities with provider mix"""
    logger.info(
        f"🎯 GLOBAL RELEVANCE ANALYSIS FOR {provider_name.upper()} (Top {top_n}):"
    )
    logger.info("=" * 100)

    # Count providers in top results
    provider_counts = {}
    for course, probability, relevance_score, field_scores in ranked_courses[:top_n]:
        provider = course.get("_provider", "unknown")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1

    logger.info(f"Provider distribution in top {top_n}: {provider_counts}")

    for i, (course, probability, relevance_score, field_scores) in enumerate(
        ranked_courses[:top_n]
    ):
        title = course.get("Title", "Unknown Title")[:70]
        category = course.get("Category", "Unknown")
        provider = course.get("_provider", "unknown")

        # Format field scores for display
        field_score_str = " | ".join([f"{k}: {v:.2f}" for k, v in field_scores.items()])

        logger.info(
            f"{i+1:2d}. [{provider.upper():<12}] Prob: {probability:.4f} | Score: {relevance_score:.4f}"
        )
        logger.info(f"     Title: {title}")
        logger.info(f"     Category: {category}")
        logger.info(f"     Field Scores: {field_score_str}")
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


def remove_duplicate_courses(courses):
    """Remove duplicate courses based on title and provider"""
    seen_courses = set()
    unique_courses = []

    for course in courses:
        # Create a unique identifier based on title and provider
        if "original_data" in course and isinstance(course["original_data"], dict):
            title = course["original_data"].get("Title", "").lower().strip()
            provider = course.get("provider", "").lower().strip()
        else:
            title = course.get("unified_data", {}).get("title", "").lower().strip()
            provider = course.get("provider", "").lower().strip()

        course_id = f"{provider}:{title}"

        if course_id not in seen_courses:
            seen_courses.add(course_id)
            unique_courses.append(course)
        else:
            logger.debug(f"Removed duplicate: {title} from {provider}")

    logger.info(f"Removed {len(courses) - len(unique_courses)} duplicate courses")
    return unique_courses


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

        # Apply GLOBAL relevance scoring to all combined results
        if combined_results:
            logger.info(
                "🎯 Applying GLOBAL relevance scoring to cross-platform results"
            )
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

        # NEW: Apply GLOBAL scoring after collecting ALL provider results
        all_documents = []
        for provider, docs in raw_documents_by_provider.items():
            for doc in docs:
                doc["_provider"] = provider  # Ensure provider info is attached
                all_documents.append(doc)

        if all_documents:
            logger.info(
                f"🎯 Applying GLOBAL relevance scoring to {len(all_documents)} documents from ALL providers"
            )
            ranked_courses = relevance_scorer.rank_courses_by_relevance(
                all_documents, user_query
            )

            # DEBUG: Show probabilities
            debug_relevance_probabilities(ranked_courses, "global_all_providers")

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

    return all_results, execution_results, raw_documents_by_provider


def save_relevance_report(all_results, user_query, output_dir):
    """Save a detailed relevance report as a text file"""
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "relevance_report.txt")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("RELEVANCE SCORING REPORT\n")
        f.write("=" * 100 + "\n")
        f.write(f"User Query: {user_query}\n")
        f.write(f"Total Courses: {len(all_results)}\n")
        f.write(f"Generated at: {datetime.utcnow().isoformat()}\n")
        f.write("=" * 100 + "\n\n")

        # Group by provider for analysis
        provider_stats = {}
        for result in all_results:
            provider = result.get("provider", "unknown")
            if provider not in provider_stats:
                provider_stats[provider] = {
                    "count": 0,
                    "total_prob": 0,
                    "total_score": 0,
                    "courses": [],
                }

            provider_stats[provider]["count"] += 1
            provider_stats[provider]["total_prob"] += result.get(
                "relevance_probability", 0
            )
            provider_stats[provider]["total_score"] += result.get("relevance_score", 0)
            provider_stats[provider]["courses"].append(result)

        # Write provider statistics
        f.write("PROVIDER DISTRIBUTION:\n")
        f.write("-" * 80 + "\n")
        for provider, stats in provider_stats.items():
            avg_prob = stats["total_prob"] / stats["count"] if stats["count"] > 0 else 0
            avg_score = (
                stats["total_score"] / stats["count"] if stats["count"] > 0 else 0
            )
            f.write(
                f"{provider.upper():<15}: {stats['count']:3d} courses | "
                f"Avg Prob: {avg_prob:.4f} | Avg Score: {avg_score:.4f}\n"
            )
        f.write("\n")

        # Write top courses by probability
        f.write("TOP 50 COURSES BY RELEVANCE PROBABILITY:\n")
        f.write("-" * 120 + "\n")

        # Sort all results by probability
        sorted_results = sorted(
            all_results, key=lambda x: x.get("relevance_probability", 0), reverse=True
        )

        for i, result in enumerate(sorted_results[:50]):
            prob = result.get("relevance_probability", 0)
            score = result.get("relevance_score", 0)
            provider = result.get("provider", "unknown")
            title = result.get("unified_data", {}).get("title", "Unknown Title")

            f.write(
                f"{i+1:2d}. [{provider.upper():<12}] Prob: {prob:.4f} | Score: {score:.4f}\n"
            )
            f.write(f"     {title}\n")

            # FIXED: Handle Skills field properly - it might be int, str, or missing
            if "original_data" in result and isinstance(result["original_data"], dict):
                orig_data = result["original_data"]
                skills_value = orig_data.get("Skills")
                if skills_value:
                    if isinstance(skills_value, str):
                        skills = skills_value[:100]
                    elif isinstance(skills_value, (int, float)):
                        skills = str(skills_value)
                    else:
                        skills = str(skills_value)[:100]
                else:
                    skills = "No skills"
                f.write(f"     Skills: {skills}\n")

            f.write("\n")

        # Write probability distribution
        f.write("\nPROBABILITY DISTRIBUTION:\n")
        f.write("-" * 80 + "\n")

        probabilities = [
            result.get("relevance_probability", 0) for result in all_results
        ]
        if probabilities:
            ranges = [
                (0.1, 1.0, "Very High"),
                (0.05, 0.1, "High"),
                (0.01, 0.05, "Medium"),
                (0.001, 0.01, "Low"),
                (0, 0.001, "Very Low"),
            ]

            for min_val, max_val, label in ranges:
                count = len([p for p in probabilities if min_val <= p < max_val])
                percentage = (count / len(probabilities)) * 100
                f.write(f"{label:<10}: {count:3d} courses ({percentage:5.1f}%)\n")

    logger.success(f"📄 Relevance report saved: {report_path}")
    return report_path


def process_batch_enrichment(all_results):
    """Process batch enrichment for all courses"""
    from src.app.data_enrichment.uniform_formatter import process_batch_enrichment
    
    if not all_results:
        return all_results
    
    # Prepare courses for batch enrichment
    courses_for_enrichment = []
    for result in all_results:
        # Only enrich courses with reasonable relevance probability (> 0.5%)
        relevance_prob = result.get("relevance_probability", 0)
        if relevance_prob >= 0.005:
            course_data = {
                **result["unified_data"],
                "provider": result["provider"],
                "original_data": result["original_data"],
                "relevance_probability": relevance_prob,
                "relevance_score": result.get("relevance_score", 0)
            }
            courses_for_enrichment.append(course_data)
        else:
            # Skip low-probability courses to save API calls
            logger.debug(f"⏭️  Skipping enrichment for low-probability course: {relevance_prob:.4f}")
    
    logger.info(f"🎯 Preparing batch enrichment for {len(courses_for_enrichment)}/{len(all_results)} courses (probability >= 0.5%)")
    
    if not courses_for_enrichment:
        logger.info("ℹ️  No courses meet the probability threshold for enrichment")
        return all_results
    
    # Process batch enrichment
    try:
        enriched_courses = process_batch_enrichment(courses_for_enrichment)
        
        # Create a mapping for quick lookup
        enriched_dict = {}
        for enriched_course in enriched_courses:
            title = enriched_course.get('title', '')
            provider = enriched_course.get('provider', '')
            key = f"{provider}:{title}"
            enriched_dict[key] = enriched_course
        
        # Update results with enriched data
        updated_count = 0
        for result in all_results:
            title = result["unified_data"].get('title', '')
            provider = result.get('provider', '')
            key = f"{provider}:{title}"
            
            if key in enriched_dict:
                enriched_course = enriched_dict[key]
                result["unified_data"] = enriched_course
                result["enrichment_applied"] = enriched_course.get("_enrichment_applied", False)
                updated_count += 1
        
        logger.info(f"✅ Batch enrichment completed: {updated_count} courses updated")
        
    except Exception as e:
        logger.error(f"❌ Batch enrichment failed: {e}")
        # Fallback: mark all as not enriched
        for result in all_results:
            result["enrichment_applied"] = False
    
    return all_results


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

            # FIRST: Collect all documents from all providers
            all_documents = []
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

                # Add provider info to each document
                for doc in sanitized_docs:
                    doc["_provider"] = provider
                    all_documents.append(doc)

            # SECOND: Apply GLOBAL relevance scoring to ALL documents
            if all_documents:
                logger.info(
                    f"🎯 Applying GLOBAL relevance scoring to {len(all_documents)} documents from ALL providers"
                )
                ranked_courses = relevance_scorer.rank_courses_by_relevance(
                    all_documents, userQuery
                )

                # DEBUG: Show probabilities
                debug_relevance_probabilities(ranked_courses, "global_all_providers")

                for (
                    course,
                    probability,
                    relevance_score,
                    field_scores,
                ) in ranked_courses:
                    provider = course.get("_provider", "unknown")
                    unified_data = unifyResponse(
                        provider, course, probability, relevance_score
                    )

                    all_results.append(
                        {
                            "provider": provider,
                            "original_data": course,
                            "unified_data": unified_data,
                            "enrichment_applied": False,  # Will be set by batch enrichment
                            "relevance_probability": probability,
                            "relevance_score": relevance_score,
                        }
                    )

        # NEW: Remove duplicate courses before enrichment
        logger.info(f"📊 Before duplicate removal: {len(all_results)} courses")
        all_results = remove_duplicate_courses(all_results)
        logger.info(f"📊 After duplicate removal: {len(all_results)} courses")

        # NEW: STEP 3: Batch enrichment for all courses
        logger.info("🤖 STEP 3: Batch enrichment...")
        all_results = process_batch_enrichment(all_results)

        # STEP 4: Save results
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

        # NEW: Save detailed relevance report as TXT file
        relevance_report_path = save_relevance_report(
            all_results, userQuery, query_output_dir
        )

        logger.success(f"✅ All files saved to {query_output_dir}")
        logger.info(f"📊 Total results: {len(all_results)}")

        # Count enriched courses
        enriched_count = sum(1 for result in all_results if result.get("enrichment_applied", False))
        logger.info(f"🎯 Courses enriched: {enriched_count}/{len(all_results)}")

        # Prepare clean results for frontend - NOW GLOBALLY SORTED BY RELEVANCE
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
                f"Enriched: {result.get('enrichment_applied', False)} | "
                f"Title: {result.get('title', 'Unknown')[:60]}"
            )

        # Create comprehensive summary
        create_relevance_summary(frontend_results, userQuery)

        # Provider distribution analysis
        provider_distribution = {}
        for result in frontend_results:
            provider = result.get('source_provider', 'unknown')
            provider_distribution[provider] = provider_distribution.get(provider, 0) + 1
        
        logger.info("🏢 PROVIDER DISTRIBUTION:")
        for provider, count in provider_distribution.items():
            logger.info(f"   {provider.upper():<12}: {count} courses")

        return {
            "query": userQuery,
            "results": frontend_results,
            "total_results": len(frontend_results),
            "enriched_courses": enriched_count,
            "provider_distribution": provider_distribution,
            "debug": debug_info,
            "output_directory": query_output_dir,
        }

    except Exception as e:
        logger.error(f"❌ Error processing query: {str(e)}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        return {"query": userQuery, "results": [], "total_results": 0, "error": str(e)}
    
