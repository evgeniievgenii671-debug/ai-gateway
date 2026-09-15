import os
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M")
TELEGRAM_SEND_MESSAGE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Пул из 4 ассистентов с ротацией по кругу
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
    try:
        data = await request.json()
        
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            user_text = data["message"]["text"]
            
            assistant = get_next_assistant()
            active_assistant_name = assistant["name"]
            
            # Динамический ответ с учетом запроса клиента
            reply_text = (
                f"[{active_assistant_name}]\n"
                f"Приветствую! Рад помочь вам с выбором. По вашему запросу («{user_text}») "
                f"могу предложить качественный кафель, эпоксидные полы и сопутствующие материалы. "
                f"Какой объем вас интересует?"
            )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    TELEGRAM_SEND_MESSAGE_URL,
                    json={"chat_id": chat_id, "text": reply_text}
                )
    except Exception as e:
        print(f"Error handling webhook: {e}")
        
    return {"ok": True}

@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    assistant = get_next_assistant()
    active_assistant_name = assistant["name"]
    print(f"WhatsApp request handled by {active_assistant_name}: {data}")
    return {"status": "received", "assistant": active_assistant_name}
