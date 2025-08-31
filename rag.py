# rag.py
import os, re, yaml
from typing import List, Dict

PLAYBOOK_PATH = os.getenv("PLAYBOOK_PATH", "playbooks.yaml")
KB_DIR = os.getenv("KB_DIR", "kb")

with open(PLAYBOOK_PATH, "r", encoding="utf-8") as f:
    _PB = yaml.safe_load(f)

def _norm(s: str) -> str:
    return (s or "").lower()

def _strip_md(text: str) -> str:
    if not text:
        return ""
    t = text
    # убираем markdown-заголовки/жирность/код
    t = re.sub(r"`{1,3}.*?`{1,3}", " ", t, flags=re.S)
    t = re.sub(r"\*\*(.*?)\*\*", r"\1", t)
    t = re.sub(r"__(.*?)__", r"\1", t)
    t = re.sub(r"^#{1,6}\s*", "", t, flags=re.M)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()

def suggest_from_playbooks(query: str):
    if query == "_list_all":
        return [k for k in _PB.keys() if k != "__index__"]
    q = _norm(query)
    best, score_best = None, 0
    for key, pb in _PB.items():
        if key == "__index__": continue
        score = sum(1 for w in pb.get("match", []) if _norm(w) in q)
        if score > score_best:
            best, score_best = pb, score
    return best

def kb_search(query: str, limit: int = 5) -> List[Dict]:
    q = _norm(query)
    out: List[Dict] = []

    # Плейбуки как база знаний
    for key, pb in _PB.items():
        if key == "__index__": continue
        text = " ".join([pb.get("title",""), *pb.get("now",[]), *pb.get("if_fail",[]), *pb.get("notes",[])])
        if any(tok in text.lower() for tok in q.split()):
            snippet = _strip_md(" ".join(pb.get("now", [])[:3]))[:300]
            out.append({"title": pb.get("title", key), "snippet": snippet, "source": f"playbook:{key}"})

    # Файлы kb/
    if os.path.isdir(KB_DIR):
        for name in os.listdir(KB_DIR):
            if not name.lower().endswith((".md",".txt")): continue
            path = os.path.join(KB_DIR, name)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                low = text.lower()
                if any(tok in low for tok in q.split()):
                    snippet = _strip_md(text)[:400]
                    out.append({"title": name, "snippet": snippet, "source": f"kb:{name}"})
            except Exception:
                continue

    out.sort(key=lambda x: (-len(x["snippet"]), x["title"]))
    return out[:limit]
