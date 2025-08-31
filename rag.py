import os, yaml
from typing import List, Dict

PLAYBOOK_PATH = os.getenv("PLAYBOOK_PATH", "playbooks.yaml")
KB_DIR = os.getenv("KB_DIR", "kb")

with open(PLAYBOOK_PATH, "r", encoding="utf-8") as f:
    _PB = yaml.safe_load(f)

def _norm(s: str) -> str:
    return (s or "").lower()

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
    # Плейбуки тоже считаем базой
    for key, pb in _PB.items():
        if key == "__index__": continue
        text = " ".join([
            pb.get("title",""),
            " ".join(pb.get("now",[])),
            " ".join(pb.get("if_fail",[])),
            " ".join(pb.get("notes",[]))
        ]).lower()
        if any(tok in text for tok in q.split()):
            out.append({
                "title": pb.get("title", key),
                "snippet": " ".join(pb.get("now", [])[:2])[:300],
                "source": f"playbook:{key}"
            })
    # Поиск по текстам в папке kb/
    if os.path.isdir(KB_DIR):
        for name in os.listdir(KB_DIR):
            if not name.lower().endswith((".md",".txt")): continue
            path = os.path.join(KB_DIR, name)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                low = text.lower()
                if any(tok in low for tok in q.split()):
                    pos = max(low.find(q.split()[0]), 0)
                    start = max(0, pos-120)
                    end = min(len(text), pos+180)
                    snippet = text[start:end].replace("\n"," ")
                    out.append({"title": name, "snippet": snippet[:300], "source": f"kb:{name}"})
            except Exception:
                continue
    out.sort(key=lambda x: (-len(x["snippet"]), x["title"]))
    return out[:limit]
