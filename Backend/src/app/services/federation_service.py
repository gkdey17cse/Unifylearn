# src/app/services/federation_service.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from app.services.plan_builder import build_plans
from app.services.db_service import find_documents
from app.services.adapters import normalize_doc
from app.utils.text_utils import string_relevance_score
import time
import os
from app.utils.config import OUTPUT_DIR
from io_utils.write_json import write_json


def _fetch_plan(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    # run a simple find() for this plan
    docs = find_documents(
        plan["db"],
        plan["coll"],
        plan.get("filter", {}),
        plan.get("projection"),
        plan.get("limit", 20),
    )
    return docs


def run_federated_query(parsed_query: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    plans = build_plans(parsed_query)
    results = []
    errors = []
    # run in parallel
    with ThreadPoolExecutor(max_workers=min(8, len(plans) or 1)) as ex:
        futures = {ex.submit(_fetch_plan, p): p for p in plans}
        for fut in as_completed(futures):
            plan = futures[fut]
            try:
                docs = fut.result()
            except Exception as e:
                errors.append({"provider": plan["provider"], "error": str(e)})
                continue
            # normalize docs
            for d in docs:
                norm = normalize_doc(plan["provider"], d)
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
            continue
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    # ranking: if user asked for top/worst by rating, use rating sort
    sort_dir = parsed_query.get("sort")
    topic = parsed_query.get("topic")
    if sort_dir in ("desc", "asc"):
        # sort by rating where available; put missing rating at end (desc) or start (asc)
        def sort_key(x):
            r = x.get("rating")
            if r is None:
                return float("-inf") if sort_dir == "asc" else float("inf")
            return r

        deduped.sort(key=sort_key, reverse=(sort_dir == "desc"))
    else:
        # default: if topic exists, use relevance heuristic then rating then platform
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
            # fallback: sort by rating desc if present
            deduped.sort(key=lambda x: x.get("rating") or 0, reverse=True)

    # apply overall limit if user specified (we fetched per-provider)
    overall_limit = parsed_query.get("limit")
    final = deduped if overall_limit is None else deduped[:overall_limit]

    took = time.time() - start
    # write output JSON (timestamped)
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
