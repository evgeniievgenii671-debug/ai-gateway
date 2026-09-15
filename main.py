import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

TELEGRAM_BOT_TOKEN = "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@app.get("/")
async def root():
    return {"status": "running", "bot": "active"}

@app.post("/")
async def handle_telegram_webhook(request: Request):
    data = await request.json()
    print("Входящий запрос от Telegram:", data)
    
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]
        print(f"Текст от пользователя {chat_id}: {user_text}")
        
        ai_reply = "Извините, ошибка генерации."
        
        if GROQ_API_KEY:
            try:
                groq_url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                 "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "user", "content": user_text}
                    ]
                }
                response = requests.post(groq_url, json=payload, headers=headers, timeout=10)
                res_json = response.json()
                
                if response.status_code == 200:
                    ai_reply = res_json["choices"][0]["message"]["content"]
                else:
                    ai_reply = f"Ошибка Groq API: {res_json.get('error', {}).get('message', 'unknown')}"
            except Exception as e:
                ai_reply = f"Ошибка подключения к AI: {str(e)}"
        else:
            ai_reply = "API ключ Groq не найден в переменных окружения."

        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        tg_payload = {
            "chat_id": chat_id,
            "text": ai_reply
        }
        tg_response = requests.post(tg_url, json=tg_payload)
        print("Ответ от Telegram API:", tg_response.status_code, tg_response.text)

    return {"ok": True}

           
