import os
import google.generativeai as genai
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M")
TELEGRAM_SEND_MESSAGE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

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
        print("WEBHOOK RECEIVED:", data)
        
        # Жесткая проверка структуры сообщения от Telegram
        if "message" in data:
            message_obj = data["message"]
            if "text" in message_obj and "chat" in message_obj:
                chat_id = message_obj["chat"]["id"]
                user_text = message_obj["text"]
                
                assistant = get_next_assistant()
                active_assistant_name = assistant["name"]
                
                system_instruction = (
                    f"Ты — {active_assistant_name}, профессиональный менеджер компании по продаже качественного кафеля "
                    f"и современных эпоксидных полов. Общайся с клиентами живо, дружелюбно, подстраивайся под их стиль речи, "
                    f"отвечай по делу, помогай с выбором и консультируй по характеристикам."
                )
                
                reply_text = ""
                try:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    prompt = f"{system_instruction}\n\nКлиент написал: {user_text}"
                    response = model.generate_content(prompt)
                    reply_text = f"[{active_assistant_name}]\n{response.text}"
                except Exception as ai_err:
                    print("AI ERROR:", ai_err)
                    reply_text = f"[{active_assistant_name}] Здравствуйте! Готов помочь вам с выбором кафеля или эпоксидных полов."

                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        TELEGRAM_SEND_MESSAGE_URL,
                        json={"chat_id": chat_id, "text": reply_text}
                    )
                    print("TELEGRAM RESPONSE STATUS:", resp.status_code, resp.text)
                    
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
