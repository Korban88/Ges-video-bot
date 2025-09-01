# rag.py
import os
import re
import json
import glob
from typing import List, Dict, Tuple
from bs4 import BeautifulSoup

from rank_bm25 import BM25Okapi

# Плейбуки остаются как быстрые «первые 2 минуты»
import yaml

PLAYBOOK_PATH = os.getenv("PLAYBOOK_PATH", "playbooks.yaml")
DOCS_DIR = os.getenv("DOCS_DIR", "docs")
DATA_DIR = os.getenv("DATA_DIR", "data")
INDEX_PATH = os.path.join(DATA_DIR, "doc_chunks.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# ---------- Вспомогательное ----------
def _norm(s: str) -> str:
    return (s or "").lower()

def _strip_md(text: str) -> str:
    if not text:
        return ""
    t = text
    t = re.sub(r"`{1,3}.*?`{1,3}", " ", t, flags=re.S)
    t = re.sub(r"\*\*(.*?)\*\*", r"\1", t)
    t = re.sub(r"__(.*?)__", r"\1", t)
    t = re.sub(r"^#{1,6}\s*", "", t, flags=re.M)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()

def _tokenize(s: str) -> List[str]:
    return re.findall(r"[a-zA-Zа-яА-Я0-9]+", s.lower())

def _chunk(text: str, size: int = 900, overlap: int = 200) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        j = min(n, i + size)
        chunks.append(text[i:j])
        i = j - overlap
        if i < 0:
            i = 0
        if i >= n:
            break
    return chunks

# ---------- Загрузка плейбуков ----------
with open(PLAYBOOK_PATH, "r", encoding="utf-8") as f:
    _PB = yaml.safe_load(f)

def suggest_from_playbooks(query: str):
    if query == "_list_all":
        return [k for k in _PB.keys() if k != "__index__"]
    q = _norm(query)
    best, score_best = None, 0
    for key, pb in _PB.items():
        if key == "__index__": 
            continue
        score = sum(1 for w in pb.get("match", []) if _norm(w) in q)
        if score > score_best:
            best, score_best = pb, score
    return best

# ---------- Чтение разных форматов ----------
def _read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _read_html(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text(" ", strip=True)

def _read_pdf(path: str) -> str:
    try:
        from pdfminer.high_level import extract_text
        return extract_text(path) or ""
    except Exception:
        return ""

def _read_md(path: str) -> str:
    return _strip_md(_read_txt(path))

def _read_any(path: str) -> str:
    low = path.lower()
    if low.endswith(".pdf"):
        return _read_pdf(path)
    if low.endswith((".html", ".htm")):
        return _read_html(path)
    if low.endswith((".md", ".markdown")):
        return _read_md(path)
    return _read_txt(path)

# ---------- Индексация документов ----------
_DOC_CHUNKS: List[Dict] = []
_BM25: BM25Okapi | None = None

def _build_index() -> Tuple[int, int]:
    """
    Возвращает: (кол-во файлов, кол-во чанков)
    """
    global _DOC_CHUNKS, _BM25
    files = []
    for ext in ("*.pdf", "*.txt", "*.md", "*.markdown", "*.html", "*.htm"):
        files.extend(glob.glob(os.path.join(DOCS_DIR, ext)))
    chunks: List[Dict] = []
    for path in sorted(files):
        try:
            text = _read_any(path)
            text = _strip_md(text)
            if not text:
                continue
            parts = _chunk(text, size=900, overlap=200)
            title = os.path.basename(path)
            for i, p in enumerate(parts):
                chunks.append({
                    "title": title,
                    "source": f"doc:{title}",
                    "path": path,
                    "chunk_id": i,
                    "text": p,
                })
        except Exception:
            continue
    _DOC_CHUNKS = chunks
    # сохраняем индекс на диск (на будущее)
    try:
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(_DOC_CHUNKS, f, ensure_ascii=False)
    except Exception:
        pass
    # строим BM25
    tokenized = [_tokenize(c["text"]) for c in _DOC_CHUNKS]
    _BM25 = BM25Okapi(tokenized) if tokenized else None
    return (len(files), len(_DOC_CHUNKS))

def ensure_index_loaded() -> None:
    global _DOC_CHUNKS, _BM25
    if _DOC_CHUNKS and _BM25:
        return
    # пробуем загрузить готовые чанки
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            _DOC_CHUNKS = json.load(f)
        tokenized = [_tokenize(c["text"]) for c in _DOC_CHUNKS]
        _BM25 = BM25Okapi(tokenized) if tokenized else None
    except Exception:
        _build_index()

def reindex_docs() -> Tuple[int, int]:
    """Публичная функция для пересборки индекса."""
    return _build_index()

# ---------- Поиск ----------
def _search_docs(query: str, limit: int = 3) -> List[Dict]:
    ensure_index_loaded()
    if not _BM25 or not _DOC_CHUNKS:
        return []
    tokens = _tokenize(query)
    if not tokens:
        return []
    scores = _BM25.get_scores(tokens)
    # топ-N
    idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]
    hits: List[Dict] = []
    for i in idxs:
        c = _DOC_CHUNKS[i]
        snippet = c["text"][:600]
        hits.append({
            "title": c["title"],
            "snippet": snippet,
            "source": c["source"]
        })
    return hits

def kb_search(query: str, limit: int = 5) -> List[Dict]:
    """
    Единый поиск: сначала плейбуки (как раньше), затем лучшие куски из документов.
    """
    q = _norm(query)
    out: List[Dict] = []

    # 1) Плейбуки (быстрые подсказки)
    for key, pb in _PB.items():
        if key == "__index__":
            continue
        text = " ".join([pb.get("title",""), *pb.get("now",[]), *pb.get("if_fail",[]), *pb.get("notes",[])])
        if any(tok in text.lower() for tok in q.split()):
            sn = _strip_md(" ".join(pb.get("now", [])[:3]))[:300]
            out.append({"title": pb.get("title", key), "snippet": sn, "source": f"playbook:{key}"})

    # 2) Документы
    doc_hits = _search_docs(query, limit=max(1, limit - len(out)))
    out.extend(doc_hits)

    return out[:limit]
