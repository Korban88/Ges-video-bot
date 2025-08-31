# GES-Video Bot (Step 1)

Минимальный Telegram-бот для видеоотдела ГЭС-2.  
Работает на Railway через вебхук, доступ ограничен по белому списку пользователей.

## Переменные окружения
- TELEGRAM_TOKEN = 8455327098:AAHDAlgk3BPCcfAp2HfG9gPbZc3Z0o__83E
- ALLOWED_USER_IDS = 347552741
- WEBHOOK_URL = https://<your-app>.up.railway.app/webhook

## Деплой
1. Создай проект на Railway, подключи репозиторий.  
2. В Variables добавь:
   - TELEGRAM_TOKEN
   - ALLOWED_USER_IDS
3. Деплой → дождись старта.  
4. Найди домен Railway: `https://<domain>.up.railway.app`.  
5. Добавь переменную `WEBHOOK_URL = https://<domain>.up.railway.app/webhook`.  
6. Перезапусти деплой.  
7. Проверка: открой `https://<domain>.up.railway.app/health` → должен вернуть `{"status":"ok"}`.  
8. Напиши боту в Telegram `/start`. Ответит только твой ID.
