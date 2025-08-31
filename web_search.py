# web_search.py
import os
import html
import requests
from typing import List, Dict

BING_API_KEY = os.getenv("BING_API_KEY")  # добавь в Railway → Variables
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"
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
    # Мягкая попытка вытащить «мясо» страницы
    try:
        from readability import Document  # из readability-lxml
        html_text = _http_get(url)
        if not html_text:
            return ""
        doc = Document(html_text)
        text = doc.summary(html_partial=False)
        # Очень грубая чистка тегов
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(text, "lxml")
        cleaned = soup.get_text(" ", strip=True)
        return cleaned[:800]
    except Exception:
        return ""

def web_search_best_snippets(query: str, limit: int = 2) -> List[Dict]:
    """
    Ищем по Bing Web Search API, забираем короткие сниппеты и пробуем вытащить текст со страниц.
    Возвращаем: [{"title":..., "snippet":..., "url":...}, ...]
    """
    if not BING_API_KEY:
        return []  # ключ не задан — молчим, чтобы не ломать бота

    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    params = {"q": query, "count": max(1, min(limit, 5)), "textDecorations": False, "mkt": "ru-RU"}
    try:
        resp = requests.get(BING_ENDPOINT, headers=headers, params=params, timeout=10)
        data = resp.json()
        items = data.get("webPages", {}).get("value", []) if isinstance(data, dict) else []
    except Exception:
        items = []

    out: List[Dict] = []
    for it in items[:limit]:
        title = it.get("name", "")
        url = it.get("url", "")
        snippet = it.get("snippet", "") or ""
        # Попробуем добрать контента со страницы
        if url:
            body = _extract_readable(url)
            if body and len(body) > len(snippet):
                snippet = body
        if not url or not title:
            continue
        out.append({
            "title": title.strip(),
            "snippet": snippet.strip()[:800],
            "url": url
        })
    return out
