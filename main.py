import os
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
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
        print("INCOMING DATA:", data)
        
        chat_id = None
        user_text = ""
        
        # Универсальный сборщик chat_id из любых типов входящих данных Telegram
        msg = data.get("message") or data.get("edited_message") or (data.get("callback_query") and data["callback_query"].get("message"))
        
        if msg and "chat" in msg:
            chat_id = msg["chat"].get("id")
            user_text = msg.get("text") or msg.get("data") or ""
            
        if not chat_id:
            print("ERROR: chat_id not found in payload")
            return {"ok": True}
            
        assistant = get_next_assistant()
        active_assistant_name = assistant["name"]
        
        reply_text = (
            f"[{active_assistant_name}] Здравствуйте! Получил ваш запрос: «{user_text}». "
            f"Помогу подобрать качественный кафель и современные эпоксидные полы под ваш проект."
        )
        
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            resp = await client.post(
                TELEGRAM_SEND_MESSAGE_URL,
                json={"chat_id": chat_id, "text": reply_text},
                headers={"Content-Type": "application/json"}
            )
            print("TELEGRAM STATUS:", resp.status_code, resp.text)
                
    except Exception as e:
        print(f"ERROR: {e}")
        
    return {"ok": True}
