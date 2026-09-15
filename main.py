import os
import requests
from fastapi import FastAPI, Request
from google import genai
from google.genai.errors import ServerError, ClientError

app = FastAPI()

TELEGRAM_BOT_TOKEN = "8680814733:AAGUbD-eHtDXy7XyR4N2Tp EQmdk0vYX_B8M"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else genai.Client()

@app.get("/")
async def root():
    return {"status": "running", "bot": "active"}

@app.post("/")
async def handle_telegram_webhook(request: Request):
    data = await request.json()
    print("Входящий запрос от Telegram:", data)
    
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"]["text"]
        print(f"Текст от пользователя {chat_id}: {user_message}")
        
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=user_message
            )
            reply_text = response.text
            print(f"Ответ от Gemini: {reply_text}")
        except (ServerError, ClientError) as e:
            print(f"Ошибка Gemini API: {e}")
            reply_text = "Сервер временно перегружен, попробуй отправить сообщение еще раз!"
        
        payload = {
            "chat_id": chat_id,
            "text": reply_text
        }
        res = requests.post(telegram_url, json=payload)
        print(f"Ответ от Telegram API: {res.status_code}, {res.text}")
        
    return {"status": "ok"}
