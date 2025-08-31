# bot_routes.py
import os
from aiogram import Router, types
from aiogram.filters import Command, CommandStart

router = Router()

ALLOWED_USER_IDS = set(int(x) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip())

def allowed(user: types.User) -> bool:
    return (not ALLOWED_USER_IDS) or (user.id in ALLOWED_USER_IDS)

@router.message(CommandStart())
async def start_cmd(m: types.Message):
    if not allowed(m.from_user):
        await m.answer("Доступ ограничен. Обратись к администратору.")
        return
    await m.answer(
        "Привет! Я GES-Video Bot — помощник видеоотдела.\n"
        "Доступные команды:\n"
        "/help — справка по использованию"
    )

@router.message(Command("help"))
async def help_cmd(m: types.Message):
    if not allowed(m.from_user):
        await m.answer("Доступ ограничен.")
        return
    await m.answer(
        "Как пользоваться:\n"
        "— Пока доступны только /start и /help.\n"
        "— На следующих шагах появятся чек-листы и диагностика."
    )
