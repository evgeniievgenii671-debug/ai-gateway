import os
import time
import httpx
from fastapi import FastAPI, Request
from google.api_core.exceptions import ResourceExhausted
from google import genai

app = FastAPI()

# Получаем токены и ключи из окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Инициализируем клиент Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.6-flash"

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def ask_gemini_with_retry(prompt: str, max_retries: int = 3) -> str:
    delay = 5
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            return response.text
        except ResourceExhausted:
            print(f"Лимит Gemini исчерпан (попытка {attempt + 1}/{max_retries}). Ждем {delay} сек...")
            if attempt == max_retries - 1:
                return "⚠️ Превышен лимит запросов к нейросети (Free Tier). Пожалуйста, подождите минутку и повторите попытку."
            time.sleep(delay)
            delay *= 2
        except Exception as e:
            print(f"Ошибка Gemini: {e}")
            return "Произошла ошибка при обращении к нейросети."
    return "Не удалось получить ответ от нейросети."

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    print(f"RECV DATA: {data}")

    try:
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            user_message = data["message"]["text"]
            user_name = data["message"]["from"].get("first_name", "User")
            
            print(f"User said: {user_message}")

            # Запрос к Gemini с защитой от лимитов
            ai_reply = ask_gemini_with_retry(user_message)
            print(f"Gemini reply: {ai_reply}")

            # Отправка ответа в Telegram через HTTP-клиент
            async with httpx.AsyncClient() as httpx_client:
                payload = {
                    "chat_id": chat_id,
                    "text": ai_reply
                }
                tg_resp = await httpx_client.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
                print(f"Telegram response: {tg_resp.text}")

    except Exception as e:
        print(f"Error handling webhook: {e}")

    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "Bot is running!"}
