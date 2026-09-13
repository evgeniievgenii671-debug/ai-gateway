import os
import requests
from fastapi import FastAPI, Request
from google import genai

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Инициализация нового клиента GenAI
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else genai.Client()

@app.post("/")
async def handle_telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"]["text"]
        
        try:
            # Генерация ответа от Gemini
            response = client.models.generate_content(model='gemini-2.5-flash', contents=user_message)
            bot_reply = response.text
        except Exception as e:
            bot_reply = f"Ошибка ИИ: {e}"
            
        # Отправка ответа в Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": bot_reply})
        
    return {"ok": True}
               
