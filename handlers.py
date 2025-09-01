import re
import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message
from aiogram import Bot
from starlette.concurrency import run_in_threadpool

router = Router()
log = logging.getLogger("ges-video-bot.handlers")

DOCS_DIR = Path("docs")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9а-яА-ЯёЁ._ \-]+")

def sanitize_filename(name: str) -> str:
    name = name.replace("/", "_").replace("\\", "_")
    name = SAFE_NAME_RE.sub("_", name)
    return (name or "file")[:120]

def allowed_extension(filename: str) -> bool:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    return ext in {"pdf", "txt", "md", "html", "htm"}

@router.message(F.document)
async def handle_document(msg: Message, bot: Bot):
    doc = msg.document
    filename = sanitize_filename(doc.file_name or "file")
    if not allowed_extension(filename):
        await msg.answer("Поддерживаю только PDF/HTML/MD/TXT. Переименуй файл с подходящим расширением.")
        return

    tg_file = await bot.get_file(doc.file_id)
    dest = DOCS_DIR / filename
    await bot.download_file(tg_file.file_path, destination=dest)

    await msg.answer(f"Файл сохранён: <code>{dest.as_posix()}</code>\nПересобираю индекс...")

    try:
        from rag import build_index
    except Exception as e:
        log.exception(f"Импорт rag.build_index не удался: {e}")
        await msg.answer("Ошибка: не удалось импортировать индексатор (rag.py). Проверь лог.")
        return

    try:
        await run_in_threadpool(build_index)
    except Exception as e:
        log.exception(f"Ошибка пересборки индекса: {e}")
        await msg.answer("Ошибка при пересборке индекса. См. логи.")
        return

    await msg.answer("Индекс пересобран ✅")

@router.message(F.text == "/reindex")
async def manual_reindex(msg: Message):
    await msg.answer("Пересобираю индекс...")
    try:
        from rag import build_index
        await run_in_threadpool(build_index)
        await msg.answer("Индекс пересобран ✅")
    except Exception as e:
        logging.exception(e)
        await msg.answer("Ошибка при пересборке индекса. См. логи.")

@router.message(F.text == "/diagnose")
async def diagnose(msg: Message):
    problems = []
    if not DOCS_DIR.exists():
        problems.append("❌ Папка docs/ не существует")
    else:
        problems.append("✅ Папка docs/ доступна")
    try:
        p = DOCS_DIR / ".writetest"
        p.write_text("ok", encoding="utf-8")
        p.unlink(missing_ok=True)
        problems.append("✅ Есть права на запись в docs/")
    except Exception:
        problems.append("❌ Нет прав на запись в docs/")
    await msg.answer("Диагностика:\n" + "\n".join(problems))
