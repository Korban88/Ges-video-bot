# web_search.py
import os
import requests
from typing import List, Dict

SERPER_API_KEY = os.getenv("SERPER_API_KEY")  # задай в Railway → Variables
SERPER_ENDPOINT = "https://google.serper.dev/search"
UA = "GES-VideoBot/1.0 (+https://example.invalid)"

def _http_get(url: str) -> str:
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": UA})
        if r.ok:
            return r.text
    except Exception:
        pass
    return ""

def _extract_readable(url: str) -> str:
    try:
        from readability import Document
        from bs4 import BeautifulSoup
        html_text = _http_get(url)
        if not html_text:
            return ""
        doc = Document(html_text)
        summary_html = doc.summary(html_partial=False)
        soup = BeautifulSoup(summary_html, "lxml")
        text = soup.get_text(" ", strip=True)
        # подрезаем, чтобы не раздуть ответ
        return text[:800]
    except Exception:
        return ""

def web_search_best_snippets(query: str, limit: int = 2) -> List[Dict]:
    """
    Ищет в Google через Serper.dev и возвращает 1–2 аккуратных сниппета с ссылками.
    Формат: [{"title":..., "snippet":..., "url":...}, ...]
    """
    if not SERPER_API_KEY:
        return []

    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {
        "q": query,
        "gl": "ru",   # география
        "hl": "ru",   # язык интерфейса
        "num": max(1, min(limit, 5))
    }

    items = []
    try:
        resp = requests.post(SERPER_ENDPOINT, headers=headers, json=payload, timeout=10)
        data = resp.json()
        items = data.get("organic", []) if isinstance(data, dict) else []
    except Exception:
        items = []

    out: List[Dict] = []
    for it in items[:limit]:
        title = (it.get("title") or "").strip()
        url = (it.get("link") or "").strip()
        snippet = (it.get("snippet") or "").strip()
        if not title or not url:
            continue
        # пытаемся вытащить более содержательный фрагмент со страницы
        body = _extract_readable(url)
        if body and len(body) > len(snippet):
            snippet = body
        out.append({"title": title, "snippet": snippet[:800], "url": url})
    return out
