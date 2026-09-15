import os
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

TELEGRAM_BOT_TOKEN = "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Используем публичный бесплатный эндпоинт для генерации текста без ключей
AI_PROXY_URL = "https://nekos.best/api/v2/chatbot" # Или альтернативный текстовый шлюз

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]
        
        reply_text = "Не удалось обработать запрос."
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Отправляем запрос на публичный шлюз чата
                response = await client.get(f"https://nekos.best/api/v2/chatbot?text={user_text}")
                if response.status_code == 200:
                    res_data = response.json()
                    reply_text = res_data.get("response", f"Эхо-ответ ИИ: {user_text}")
                else:
                    reply_text = f"Получено сообщение: {user_text}"
            except Exception as e:
                reply_text = f"Эхо: {user_text}"
            
            # Отправка ответа в Telegram
            await client.post(
                TELEGRAM_API_URL,
                json={"chat_id": chat_id, "text": reply_text}
            )
            
    return {"ok": True}
