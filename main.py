import os
import logging
from pathlib import Path

from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from starlette.concurrency import run_in_threadpool

# ===== Настройки =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # https://<your-domain>/webhook
WEBHOOK_PATH = "/webhook"

# Логи
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("ges-video-bot")

# Папка docs
DOCS_DIR = Path("docs")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Aiogram
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Подключаем наши хендлеры
from handlers import router as handlers_router  # noqa: E402
dp.include_router(handlers_router)

# FastAPI
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    # Устанавливаем вебхук (если указан URL)
    if WEBHOOK_URL:
        set_res = await bot.set_webhook(url=WEBHOOK_URL + WEBHOOK_PATH, drop_pending_updates=True)
        log.info(f"Webhook set: {set_res} → {WEBHOOK_URL+WEBHOOK_PATH}")
    else:
        log.warning("WEBHOOK_URL не задан — проверь переменные окружения.")

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    try:
        update = Update.model_validate(data)
    except Exception as e:
        log.exception(f"Update validate error: {e}")
        return Response(status_code=200)
    # Логируем тип апдейта для отладки
    kind = next((k for k, v in data.items() if k in ("message", "edited_message", "callback_query")), "unknown")
    log.info(f"Incoming update: {kind}")
    await dp.feed_update(bot, update)
    return Response(status_code=200)

# Healthcheck
@app.get("/")
async def root():
    return {"ok": True, "service": "GES-Video Bot"}
