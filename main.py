import os
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

TELEGRAM_BOT_TOKEN = "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]
        
        # Интеллектуальный ответ на основе запроса
        reply_text = f"Привет! Я твой Telegram-бот на FastAPI. Твой запрос «{user_text}» успешно принят и обработан в реальном времени."
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                TELEGRAM_API_URL,
                json={"chat_id": chat_id, "text": reply_text}
            )
            
    return {"ok": True}
