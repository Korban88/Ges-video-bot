# main.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update
from aiogram.fsm.storage.memory import MemoryStorage

from bot_routes import router as bot_router

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://<your-domain>.up.railway.app/webhook

if not TELEGRAM_TOKEN:
    raise RuntimeError("Env TELEGRAM_TOKEN is not set")

app = FastAPI(title="GES-Video Bot")

bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(bot_router)

@app.on_event("startup")
async def on_startup():
    # Ставим вебхук (если задан). При первом старте без WEBHOOK_URL — просто поднимется сервер.
    if WEBHOOK_URL:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()

@app.get("/")
async def root():
    return PlainTextResponse("OK")

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})

async def _process_update(request: Request):
    # Надёжный парсинг: сначала читаем «сырое» тело.
    raw = await request.body()
    if not raw:
        return JSONResponse({"ok": True})
    try:
        # Pydantic v2: парсим прямо из JSON-строки.
        update = Update.model_validate_json(raw)
    except Exception as e:
        # Не валим сервер, просто подтверждаем получение и логируем.
        print("Update parse error:", e)
        try:
            data = await request.json()
            print("Bad update payload:", data)
        except Exception:
            print("Body (bytes):", raw[:500])
        return JSONResponse({"ok": True})
    try:
        await dp.feed_update(bot, update)
    except Exception as e:
        # Если обработчик упал — тоже не даём 500.
        print("Update handling error:", e)
    return JSONResponse({"ok": True})

@app.post("/webhook")
async def telegram_webhook(request: Request):
    return await _process_update(request)

# На всякий случай: если вдруг вебхук укажут на корень — примем и там.
@app.post("/")
async def telegram_webhook_root(request: Request):
    return await _process_update(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
