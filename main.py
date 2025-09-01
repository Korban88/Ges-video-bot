import os
import logging
from pathlib import Path

from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher
from aiogram.types import Update

# ===== Настройки =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # например: https://ges-video-bot-production.up.railway.app
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
if not BOT_TOKEN:
    # Не роняем приложение, но явно логируем проблему, чтобы не упасть на импорте
    log.warning("ENV BOT_TOKEN пуст — боту будет нечем авторизоваться.")
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()

# Подключаем хендлеры (делаем внутри try, чтобы увидеть понятную ошибку)
try:
    from handlers import router as handlers_router  # noqa: E402
    dp.include_router(handlers_router)
except Exception as e:
    log.exception(f"Ошибка при импорте handlers: {e}")
    # Не бросаем исключение, чтобы увидеть ответ /health и логи
    # но вебхук работать не будет, пока не починим импорт.

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    if not BOT_TOKEN:
        log.error("BOT_TOKEN не задан — вебхук не будет установлен.")
        return
    if not WEBHOOK_URL:
        log.error("WEBHOOK_URL не задан — вебхук не будет установлен.")
        return
    try:
        set_res = await bot.set_webhook(
            url=WEBHOOK_URL + WEBHOOK_PATH,
            drop_pending_updates=True,
        )
        log.info(f"Webhook set: {set_res} → {WEBHOOK_URL + WEBHOOK_PATH}")
    except Exception as e:
        log.exception(f"Не удалось установить вебхук: {e}")


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    # Защитимся: если bot/dispatcher не инициализированы — отвечаем 200 и логируем
    if bot is None:
        log.error("BOT_TOKEN отсутствует, bot не инициализирован — апдейты не обрабатываются.")
        return Response(status_code=200)

    data = await request.json()
    try:
        update = Update.model_validate(data)
    except Exception as e:
        log.exception(f"Update validate error: {e}")
        return Response(status_code=200)

    kind = next((k for k in data.keys() if k in ("message", "edited_message", "callback_query")), "unknown")
    log.info(f"Incoming update: {kind}")
    try:
        await dp.feed_update(bot, update)
    except Exception as e:
        log.exception(f"Ошибка обработки апдейта: {e}")
    return Response(status_code=200)


@app.get("/")
async def root():
    return {"ok": True, "service": "GES-Video Bot"}


@app.get("/health")
async def health():
    return {
        "ok": True,
        "has_bot": bot is not None,
        "webhook_path": WEBHOOK_PATH,
    }
