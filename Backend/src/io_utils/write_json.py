# src/io/write_json.py
import os, json, datetime
from typing import Any, Dict


def write_json(payload: Dict[str, Any], output_dir: str = "./results") -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    fname = os.path.join(output_dir, f"query_{ts}.json")
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return fname
