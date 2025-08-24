# src/app/services/federation_service.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from src.app.services.plan_builder import build_plans, PROVIDERS
from src.app.services.db_service import find_documents
from src.app.services.adapters import normalize_doc
from src.app.utils.text_utils import string_relevance_score
import time
import os
from src.app.utils.config import OUTPUT_DIR
from src.io_utils.write_json import write_json
import logging


def _fetch_plan(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Execute a single plan. The plan is expected to have:
    - db, coll
    - filter (dict) optional
    - projection (dict) optional
    - limit (int) optional
    This works for both rule-based plans (from build_plans) and LLM-generated plans.
    """
    db = plan.get("db")
    coll = plan.get("coll")
    filt = plan.get("filter", {}) or {}
    proj = plan.get("projection", None)
    limit = plan.get("limit", 20)
    # Defensive defaults
    try:
        docs = find_documents(db, coll, filt, proj, limit)
        return docs
    except Exception as e:
        logging.exception("Error executing plan for %s.%s: %s", db, coll, str(e))
        raise


def run_federated_query(
    parsed_query: Dict[str, Any], llm_plans: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Run federated query. If llm_plans is provided and non-empty, we use them.
    Otherwise we fall back to build_plans(parsed_query).
    """
    start = time.time()

    # Choose plans: prefer validated llm_plans, otherwise build from parsed_query
    if llm_plans:
        plans = llm_plans
    else:
        plans = build_plans(parsed_query)

    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    # run in parallel
    with ThreadPoolExecutor(max_workers=min(8, len(plans) or 1)) as ex:
        futures = {ex.submit(_fetch_plan, p): p for p in plans}
        for fut in as_completed(futures):
            plan = futures[fut]
            try:
                docs = fut.result()
            except Exception as e:
                errors.append(
                    {
                        "provider": plan.get("provider", plan.get("coll")),
                        "error": str(e),
                    }
                )
                continue
            # normalize docs
            for d in docs:
                norm = normalize_doc(plan.get("provider", ""), d)
                results.append(norm)

    # dedupe by URL (if present), else by platform+title
    seen = set()
    deduped = []
    for r in results:
        key = None
        if r.get("url"):
            key = r["url"]
        elif r.get("title"):
            key = f"{r.get('platform')}::{r.get('title')}".lower()
        else:
            # skip documents without identifiable key
            continue
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    # ranking: if user asked for top/worst by rating, use rating sort
    sort_dir = parsed_query.get("sort")
    topic = parsed_query.get("topic")
    if sort_dir in ("desc", "asc"):

        def sort_key(x):
            r = x.get("rating")
            if r is None:
                return float("-inf") if sort_dir == "asc" else float("inf")
            return r

        deduped.sort(key=sort_key, reverse=(sort_dir == "desc"))
    else:
        if topic:
            deduped.sort(
                key=lambda x: (
                    string_relevance_score(
                        (x.get("title") or "")
                        + " "
                        + (x.get("snippet") or "")
                        + " "
                        + " ".join(x.get("skills") or []),
                        topic,
                    ),
                    x.get("rating") or 0,
                ),
                reverse=True,
            )
        else:
            deduped.sort(key=lambda x: x.get("rating") or 0, reverse=True)

    # apply overall limit if user specified (we fetched per-provider)
    overall_limit = parsed_query.get("limit")
    final = deduped if overall_limit is None else deduped[:overall_limit]

    took = time.time() - start
    fname = write_json(
        {
            "query": parsed_query.get("raw"),
            "parsed": parsed_query,
            "results_count": len(final),
            "results": final,
            "errors": errors,
            "took_seconds": took,
        },
        output_dir=OUTPUT_DIR,
    )
    return {
        "results": final,
        "meta": {"took_seconds": took, "out_file": fname, "errors": errors},
    }
