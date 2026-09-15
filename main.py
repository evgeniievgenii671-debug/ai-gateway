import os
import logging
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
import httpx

# Настройка логирования, чтобы сразу видеть всё в консоли Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Читаем токен из окружения с защитой от пустоты
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

class TelegramUpdate(BaseModel):
    update_id: int
    message: dict = None

@app.get("/")
async def root():
    return {"status": "online", "service": "ai-gateway"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Invalid JSON received: {e}")
        return Response(status_code=200)

    # Безопасный парсинг входящего апдейта
    message = data.get("message")
    if not message:
        return Response(status_code=200)

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")

    if not chat_id:
        return Response(status_code=200)

    # Жесткое приведение chat_id к числу во избежание 400 ошибок от Telegram
    try:
        safe_chat_id = int(chat_id)
    except (ValueError, TypeError):
        logger.error(f"Invalid chat_id format: {chat_id}")
        return Response(status_code=200)

    # Формируем ответ (здесь задействована мультиагентная логика или заглушка)
    response_text = f"Эхо-защита: получено твое сообщение -> {text}"

    # Безопасная отправка сообщения в Telegram через асинхронный клиент
    payload = {
        "chat_id": safe_chat_id,
        "text": response_text
        # Умышленно убран parse_mode, чтобы Markdown не ломал отправку
    }

    async with httpx.AsyncClient() as client:
        try:
            tg_response = await client.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10.0)
            logger.info(f"TELEGRAM STATUS: {tg_response.status_code} | RESPONSE: {tg_response.text}")
        except Exception as e:
            logger.error(f"Failed to send message to Telegram: {e}")

    return Response(status_code=200)
