import os
from fastapi import FastAPI, Request
import google.generativeai as genai
import requests

app = FastAPI()

# Считываем переменные окружения
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Настраиваем Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Формируем URL для отправки сообщений в Telegram
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]
        
        try:
            # Генерация ответа через Gemini
            response = model.generate_content(user_text)
            ai_reply = response.text
        except Exception as e:
            ai_reply = f"Ошибка генерации ответа: {e}"
            
        # Отправка ответа пользователю в Telegram
        payload = {
            "chat_id": chat_id, 
            "text": ai_reply
        }
        requests.post(TELEGRAM_API_URL, json=payload)
        
    return {"ok": True}

@app.get("/")
def home():
    return {"status": "Bot is running!"}
