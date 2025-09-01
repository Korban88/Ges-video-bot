import logging
from pathlib import Path

log = logging.getLogger("ges-video-bot.rag")
DOCS_DIR = Path("docs")
INDEX_DIR = Path("index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

def build_index():
    files = list(DOCS_DIR.glob("**/*"))
    text_like = [p for p in files if p.suffix.lower() in {".pdf", ".txt", ".md", ".html", ".htm"}]
    log.info(f"RAG: собираю индекс из {len(text_like)} файлов...")
    # TODO: здесь ваша реальная сборка BM25
    (INDEX_DIR / "BUILD_OK").write_text(f"indexed {len(text_like)} files")
    log.info("RAG: индекс готов.")
