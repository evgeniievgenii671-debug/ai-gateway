import os
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

# Твои авторизационные данные и эндпоинт Google Cloud
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
        
        reply_text = "Не удалось получить ответ от ИИ."
        
        # Формируем заголовки под сервисный аккаунт
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
                response = await client.post(GEMINI_API_URL, json=payload, headers=headers)
                
                if response.status_code == 200:
                    res_json = response.json()
                    # Извлекаем сгенерированный текст из ответа Google API
                    reply_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    # Если ключ всё же отклонен облаком, пишем точный статус для контроля
                    reply_text = f"Ошибка доступа Google (Код {response.status_code}): проверьте права сервисного аккаунта."
            except Exception as e:
                reply_text = f"Ошибка соединения: {str(e)}"
            
            # Отправляем итоговый ответ обратно в Telegram
            await client.post(
                TELEGRAM_API_URL,
                json={"chat_id": chat_id, "text": reply_text}
            )
            
    return {"ok": True}
