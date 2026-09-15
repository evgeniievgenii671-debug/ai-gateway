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
    try:
        data = await request.json()
        
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            user_text = data["message"]["text"]
            
            assistant = get_next_assistant()
            active_assistant_name = assistant["name"]
            
            system_instruction = (
                f"Ты — {active_assistant_name}, профессиональный менеджер компании по продаже качественного кафеля "
                f"и современных эпоксидных полов. Общайся с клиентами живо, дружелюбно, подстраивайся под их стиль речи, "
                f"отвечай по делу, помогай с выбором и консультируй по характеристикам."
            )
            
            reply_text = ""
            
            # Прямой запрос к Gemini API через HTTP
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "contents": [{
                        "parts": [{"text": f"{system_instruction}\n\nКлиент написал: {user_text}"}]
                    }]
                }
                
                ai_resp = await client.post(GEMINI_URL, json=payload)
                if ai_resp.status_code == 200:
                    ai_data = ai_resp.json()
                    try:
                        ai_text = ai_data["candidates"][0]["content"]["parts"][0]["text"]
                        reply_text = f"[{active_assistant_name}]\n{ai_text}"
                    except Exception:
                        reply_text = f"[{active_assistant_name}] Здравствуйте! Готов помочь с выбором кафеля и эпоксидных полов."
                else:
                    reply_text = f"[{active_assistant_name}] Приветствую! Подскажите, какой объем кафеля или эпоксидных полов вас интересует?"

                # Отправка ответа в Telegram
                await client.post(
                    TELEGRAM_SEND_MESSAGE_URL,
                    json={"chat_id": chat_id, "text": reply_text}
                )
                
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        
    return {"ok": True}

@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    assistant = get_next_assistant()
    active_assistant_name = assistant["name"]
    print(f"WhatsApp request handled by {active_assistant_name}: {data}")
    return {"status": "received", "assistant": active_assistant_name}
