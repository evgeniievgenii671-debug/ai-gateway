import os
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M")
TELEGRAM_SEND_MESSAGE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

AI_ASSISTANTS = [
    {"id": 1, "name": "Ассистент-Альфа"},
    {"id": 2, "name": "Ассистент-Бета"},
    {"id": 3, "name": "Ассистент-Гамма"},
    {"id": 4, "name": "Ассистент-Дельта"}
]

current_index = 0

def get_next_assistant():
    global current_index
    assistant = AI_ASSISTANTS[current_index]
    current_index = (current_index + 1) % len(AI_ASSISTANTS)
    return assistant

@app.post("/webhook")
async def telegram_webhook(request: Request):
    print("--- WEBHOOK TRIGGERED ---")
    try:
        data = await request.json()
        print("DATA RECEIVED:", data)
        
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            user_text = data["message"]["text"]
            
            assistant = get_next_assistant()
            active_assistant_name = assistant["name"]
            print(f"Assigned to: {active_assistant_name}, Text: {user_text}")
            
            reply_text = f"[{active_assistant_name}] Привет! Обрабатываю ваш запрос по кафелю и эпоксидным полам..."

            async with httpx.AsyncClient(timeout=10.0) as client:
                # Сначала шлем быстрый предварительный ответ, чтобы проверить связь с Telegram
                resp = await client.post(
                    TELEGRAM_SEND_MESSAGE_URL,
                    json={"chat_id": chat_id, "text": reply_text}
                )
                print("TELEGRAM INITIAL SEND STATUS:", resp.status_code, resp.text)
                
    except Exception as e:
        print(f"CRITICAL EXCEPTION: {e}")
        
    return {"ok": True}

@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    assistant = get_next_assistant()
    return {"status": "received", "assistant": assistant["name"]}
