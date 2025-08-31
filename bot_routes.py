# bot_routes.py
import os
from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Command, CommandStart

from prompts import TROUBLESHOOT_TEMPLATE
from rag import kb_search, suggest_from_playbooks
from web_search import web_search_best_snippets

router = Router()

ALLOWED_USER_IDS = set(int(x) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip())
ADMINS = set(int(x) for x in os.getenv("ADMINS", "").split(",") if x.strip())

def allowed(user: types.User) -> bool:
    return (not ALLOWED_USER_IDS) or (user.id in ALLOWED_USER_IDS)

@router.message(CommandStart())
async def start_cmd(m: types.Message):
    if not allowed(m.from_user):
        await m.answer("Доступ ограничен. Обратись к администратору.")
        return
    await m.answer(
        "Привет! Я GES-Video Bot.\n"
        "Команды:\n"
        "/help — справка\n"
        "/playbooks — быстрые чек-листы\n"
        "/kb [запрос] — поиск по базе\n"
        "/diagnose [описание] — диагностика проблемы\n"
        "Примеры:\n"
        "/kb pixera output не видит дисплей\n"
        "/diagnose С5, плазма 65\", оптика Kramer 50м, No Signal"
    )

@router.message(Command("help"))
async def help_cmd(m: types.Message):
    if not allowed(m.from_user):
        await m.answer("Доступ ограничен.")
        return
    await m.answer(
        "Примеры:\n"
        "/playbooks — список чек-листов\n"
        "/kb pixera output не видит дисплей — поиск по базе\n"
        "/diagnose С5, плазма 65\", оптика Kramer 50м, No Signal — диагностика"
    )

@router.message(Command("playbooks"))
async def playbooks_cmd(m: types.Message):
    if not allowed(m.from_user):
        await m.answer("Доступ ограничен.")
        return
    items = suggest_from_playbooks("_list_all")
    text = "Доступные плейбуки:\n" + "\n".join(f"— {x}" for x in items)
    await m.answer(text)

@router.message(Command("kb"))
async def kb_cmd(m: types.Message):
    if not allowed(m.from_user):
        await m.answer("Доступ ограничен.")
        return
    q = m.text.partition(" ")[2].strip()
    if not q:
        await m.answer("Укажи запрос: /kb pixera outputs не видит дисплей")
        return
    hits = kb_search(q, limit=3)
    if not hits:
        await m.answer("В локальной базе пока ничего не нашёл. Попробуй /diagnose — дам чек-лист и варианты.")
        return
    out = []
    for h in hits:
        out.append(f"• <b>{h['title']}</b>\n{h['snippet']}\n— {h['source']}")
    await m.answer("\n\n".join(out), disable_web_page_preview=True)

@router.message(Command("diagnose"))
async def diagnose_cmd(m: types.Message):
    if not allowed(m.from_user):
        await m.answer("Доступ ограничен.")
        return
    description = m.text.partition(" ")[2].strip()
    if not description:
        await m.answer("Опиши проблему после команды. Пример:\n/diagnose С5, 4К проектор через Teranex, нет картинки")
        return

    playbook = suggest_from_playbooks(description)
    kb_hits = kb_search(description, limit=2)
    web_hits = web_search_best_snippets(description, limit=2)  # всегда даём 1–2 источника из интернета

    text = TROUBLESHOOT_TEMPLATE(
        description=description,
        playbook=playbook,
        kb_hits=kb_hits,
        web_hits=web_hits,
    )
    await m.answer(text, disable_web_page_preview=True)
