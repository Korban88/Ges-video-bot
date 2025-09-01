import logging
from pathlib import Path

log = logging.getLogger("ges-video-bot.rag")
DOCS_DIR = Path("docs")
INDEX_DIR = Path("index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

def build_index():
    """
    Пример: перечитать все файлы из docs/ и пересобрать индекс BM25.
    Здесь просто считаем размер и пишем метку, чтобы видеть в логах.
    Замените на свою функцию сборки индекса.
    """
    files = list(DOCS_DIR.glob("**/*"))
    text_like = [p for p in files if p.suffix.lower() in {".pdf", ".txt", ".md", ".html", ".htm"}]
    log.info(f"RAG: собираю индекс из {len(text_like)} файлов...")
    # TODO: ваша логика: извлечь текст, токенизировать, обучить BM25, сохранить артефакты в INDEX_DIR
    (INDEX_DIR / "BUILD_OK").write_text(f"indexed {len(text_like)} files")
    log.info("RAG: индекс готов.")
