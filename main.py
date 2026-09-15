import os
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M")
TELEGRAM_SEND_MESSAGE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

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
        print("INCOMING TELEGRAM DATA:", data)  # Вывод в лог Render для проверки
        
        chat_id = None
        user_text = ""
        
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_text = data["message"].get("text", "[нетекстовое сообщение]")
        elif "edited_message" in data:
            chat_id = data["edited_message"]["chat"]["id"]
            user_text = data["edited_message"].get("text", "[ред. сообщение]")
            
        if chat_id:
            assistant = get_next_assistant()
            active_assistant_name = assistant["name"]
            
            reply_text = (
                f"[{active_assistant_name}]\n"
                f"Ваше сообщение получено: «{user_text}». "
                f"Консультируем по кафелю и эпоксидным полам. Чем помочь?"
            )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    TELEGRAM_SEND_MESSAGE_URL,
                    json={"chat_id": chat_id, "text": reply_text}
                )
                print("TELEGRAM SEND STATUS:", res.status_code, res.text)
                
    except Exception as e:
        print(f"CRITICAL ERROR IN WEBHOOK: {e}")
        
    return {"ok": True}

@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    assistant = get_next_assistant()
    active_assistant_name = assistant["name"]
    print(f"WhatsApp request handled by {active_assistant_name}: {data}")
    return {"status": "received", "assistant": active_assistant_name}
