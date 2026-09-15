import os
import requests
from fastapi import FastAPI, Request
from google import genai

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else genai.Client()

@app.get("/")
async def root():
    return {"status": "running", "bot": "active"}

@app.post("/")
async def handle_telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"]["text"]
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message
        )
        reply_text = response.text
        
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": reply_text
        }
        requests.post(telegram_url, json=payload)
        
    return {"status": "ok"}
