import os
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

TELEGRAM_BOT_TOKEN = "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M"
TELEGRAM_SEND_MESSAGE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Пул из 4 ассистентов для отказоустойчивости (ротация по кругу)
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
    data = await request.json()
    
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]
        
        assistant = get_next_assistant()
        active_assistant_name = assistant["name"]
        
        reply_text = f"🎙 Telegram | Ответ от {active_assistant_name}: «{user_text}»"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                TELEGRAM_SEND_MESSAGE_URL,
                json={"chat_id": chat_id, "text": reply_text}
            )
            
    return {"ok": True}

@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    
    # Обработка входящего сообщения от WhatsApp API / шлюза
    assistant = get_next_assistant()
    active_assistant_name = assistant["name"]
    
    # Здесь будет логика отправки ответа обратно в WhatsApp
    print(f"WhatsApp request handled by {active_assistant_name}: {data}")
    
    return {"status": "received", "assistant": active_assistant_name}
