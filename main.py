import os
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M")
TELEGRAM_SEND_MESSAGE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

print("DEBUG URL:", TELEGRAM_SEND_MESSAGE_URL)

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
        
        chat_id = None
        user_text = ""
        
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_text = data["message"].get("text", "[нетекстовое сообщение]")
        elif "edited_message" in data:
            chat_id = data["edited_message"]["chat"]["id"]
            user_text = data["edited_message"].get("text", "[отредактировано]")
        elif "callback_query" in data:
            chat_id = data["callback_query"]["message"]["chat"]["id"]
            user_text = data["callback_query"].get("data", "[callback]")
            
        if not chat_id:
            print("ERROR: Не удалось извлечь chat_id из структуры:", data)
            return {"ok": True}
            
        assistant = get_next_assistant()
        active_assistant_name = assistant["name"]
        print(f"Target chat_id: {chat_id} | Assigned to: {active_assistant_name} | Text: {user_text}")
        
        reply_text = (
            f"[{active_assistant_name}] Здравствуйте! Получил ваш запрос: «{user_text}». "
            f"Помогу подобрать качественный кафель и современные эпоксидные полы под ваш проект."
        )
        
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            resp = await client.post(
                TELEGRAM_SEND_MESSAGE_URL,
                json={"chat_id": chat_id, "text": reply_text}
            )
            print("TELEGRAM SEND STATUS:", resp.status_code)
            print("TELEGRAM RESPONSE:", resp.text)
                
    except Exception as e:
        print(f"CRITICAL EXCEPTION: {e}")
        
    return {"ok": True}

@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    assistant = get_next_assistant()
    return {"status": "received", "assistant": assistant["name"]}
