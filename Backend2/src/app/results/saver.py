import os
import json
from datetime import datetime


def save_results(user_query, debug_info, all_results, output_dir="./results"):
    """
    Save results to JSON file
    """
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = os.path.join(output_dir, f"responses_{ts}.json")

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(
            {"query": user_query, "debug": debug_info, "results": all_results},
            fh,
            ensure_ascii=False,
            indent=2,
        )

    return out_path
