import os
from fastapi import FastAPI, Request
import httpx
import google.generativeai as genai

app = FastAPI()

# Инициализация официального SDK Gemini
GEMINI_API_KEY = "AQ.Ab8RN6Ibr6JuJVb63jhhP0kGWlkqnVEWIB2GwewhEU7wiZR2vw"
genai.configure(api_key=GEMINI_API_KEY)

# Используем стабильную модель
model = genai.GenerativeModel('gemini-1.5-flash')

TELEGRAM_BOT_TOKEN = "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]
        
        try:
            # Генерация ответа через официальный SDK (без кривых HTTP-запросов)
            response = model.generate_content(user_text)
            reply_text = response.text if response and response.text else "Пустой ответ от нейросети."
        except Exception as e:
            reply_text = f"Ошибка генерации: {str(e)}"
        
        # Отправка ответа в Telegram
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                TELEGRAM_API_URL,
                json={"chat_id": chat_id, "text": reply_text}
            )
            
    return {"ok": True}
