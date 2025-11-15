# src/app/results/saver.py
import os
import json
from datetime import datetime
from bson import json_util


def save_results(user_query, debug_info, all_results, output_dir="./results"):
    """
    Save complete debug results to a file (optional, for backward compatibility)
    """
    os.makedirs(output_dir, exist_ok=True)
    debug_path = os.path.join(output_dir, "debug_results.json")

    result_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_query": user_query,
        "debug_info": debug_info,
        "all_results": all_results,
    }

    with open(debug_path, "w", encoding="utf-8") as fh:
        json.dump(result_data, fh, default=json_util.default, ensure_ascii=False, indent=2)

    return debug_path