import os
from fastapi import FastAPI, Request
import google.generativeai as genai
import requests

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        print("RECV DATA:", data)
        
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            user_text = data["message"]["text"]
            print(f"User said: {user_text}")
            
            # Генерация ответа через Gemini
            response = model.generate_content(user_text)
            ai_reply = response.text
            print(f"Gemini reply: {ai_reply}")
            
            # Отправка ответа в Telegram
            payload = {"chat_id": chat_id, "text": ai_reply}
            r = requests.post(TELEGRAM_API_URL, json=payload)
            print("Telegram response:", r.text)
            
    except Exception as e:
        print("ERROR:", str(e))
        
    return {"ok": True}

@app.get("/")
def home():
    return {"status": "Bot is running!"}
