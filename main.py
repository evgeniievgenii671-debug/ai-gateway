import os
import json
import time
from fastapi import FastAPI, Request
import httpx
from google import genai

app = FastAPI()

client = genai.Client()

TELEGRAM_BOT_TOKEN = "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]
        
        reply_text = "⚠️ Ошибка связи с нейросетью."
        
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=user_text,
            )
            if response and response.text:
                reply_text = response.text
        except Exception as e:
            print(f"Ошибка: {e}")

        async with httpx.AsyncClient() as httpx_client:
            await httpx_client.post(
                TELEGRAM_API_URL,
                json={"chat_id": chat_id, "text": reply_text}
            )
            
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "bot is running"}
