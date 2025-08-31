# misses.py
import os, json, time
from typing import List, Dict

DATA_DIR = os.getenv("DATA_DIR", "data")
MISSES_PATH = os.path.join(DATA_DIR, "misses.json")

os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(MISSES_PATH):
    with open(MISSES_PATH, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False)

def log_miss(kind: str, query: str, user_id: int, chat_id: int, extra: Dict = None) -> None:
    rec = {
        "ts": int(time.time()),
        "kind": kind,      # "kb" или "diagnose"
        "query": query,
        "user_id": user_id,
        "chat_id": chat_id,
        "extra": extra or {},
    }
    try:
        with open(MISSES_PATH, "r+", encoding="utf-8") as f:
            arr = json.load(f)
            arr.insert(0, rec)
            f.seek(0); f.truncate()
            json.dump(arr[:2000], f, ensure_ascii=False)  # храним последние 2000
    except Exception:
        pass

def list_misses(limit: int = 30) -> List[Dict]:
    try:
        with open(MISSES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)[:limit]
    except Exception:
        return []

def clear_misses() -> None:
    try:
        with open(MISSES_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)
    except Exception:
        pass
