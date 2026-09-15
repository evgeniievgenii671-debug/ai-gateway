import os
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

# Вставь свой новый ключ на AIza... прямо сюда в кавычки
GEMINI_API_KEY = "AIzaAQ.Ab8RN6Ibr6JuJVb63jhhP0kGwlkqnVEWIB2GwewhEU7wiZR2vw"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

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
            async with httpx.AsyncClient() as client:
                ai_response = await client.post(
                    GEMINI_URL,
                    json={
                        "contents": [{
                            "parts": [{"text": user_text}]
                        }]
                    },
                    timeout=10.0
                )
                
                if ai_response.status_code == 200:
                    res_json = ai_response.json()
                    reply_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    reply_text = f"Ошибка API: {ai_response.status_code}"
        except Exception as e:
            reply_text = f"Ошибка: {str(e)}"

        async with httpx.AsyncClient() as httpx_client:
            await httpx_client.post(
                TELEGRAM_API_URL,
                json={"chat_id": chat_id, "text": reply_text}
            )
            
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "bot is running"}
