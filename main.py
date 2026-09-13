import os
import requests
from fastapi import FastAPI, Request
import google.generativeai as genai

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GATEWAY_URL = os.getenv("GATEWAY_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@app.on_event("startup")
def set_telegram_webhook():
    if TELEGRAM_BOT_TOKEN and GATEWAY_URL:
        webhook_url = f"{GATEWAY_URL.rstrip('/')}/webhook/telegram"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"
        try:
            response = requests.get(url)
            print("Webhook setup response:", response.json())
        except Exception as e:
            print("Failed to set webhook:", e)

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            
            if text and TELEGRAM_BOT_TOKEN:
                reply_text = "Не удалось обработать запрос."
                if GEMINI_API_KEY:
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(text)
                        reply_text = response.text
                    except Exception as ai_err:
                        reply_text = f"Ошибка ИИ: {str(ai_err)}"
                
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                requests.post(url, json={"chat_id": chat_id, "text": reply_text})
    except Exception as e:
        print(f"Webhook error: {e}")
        
    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "AI Gateway is running"}
