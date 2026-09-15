import os
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

# Используем твой OAuth/Service Account токен в заголовках
GEMINI_CREDENTIAL = "AQ.Ab8RN6Ibr6JuJVb63jhhP0kGWlkqnVEWIB2GwewhEU7wiZR2vw"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

TELEGRAM_BOT_TOKEN = "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]
        
        reply_text = "Ошибка генерации ответа."
        
        # Отправляем прямой запрос к Gemini с правильным OAuth-токеном в Bearer
        headers = {
            "Authorization": f"Bearer {GEMINI_CREDENTIAL}",
            "Content-Type": "application/json"
        }
        payload = {
            "contents": [{
                "parts": [{"text": user_text}]
            }]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                ai_response = await client.post(GEMINI_API_URL, json=payload, headers=headers)
                if ai_response.status_code == 200:
                    res_data = ai_response.json()
                    # Извлекаем текст ответа из структуры ответа Google API
                    reply_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    reply_text = f"Ошибка API: {ai_response.status_code} - {ai_response.text}"
            except Exception as e:
                reply_text = f"Ошибка соединения: {str(e)}"
            
            # Отправляем результат обратно в Telegram
            await client.post(
                TELEGRAM_API_URL,
                json={"chat_id": chat_id, "text": reply_text}
            )
            
    return {"ok": True}
