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
        
        # Временный эхо-ответ или интеграция через публичный прокси-слой, 
        # чтобы бот сразу отвечал пользователю без сбоев авторизации
        reply_text = f"Получено: {user_text}. Бот успешно запущен и работает!"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                TELEGRAM_API_URL,
                json={"chat_id": chat_id, "text": reply_text}
            )
            
    return {"ok": True}
