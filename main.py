import os
import time
import httpx
from fastapi import FastAPI, Request
from google import genai

app = FastAPI()

# Получаем токены и ключи из окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Инициализируем клиент Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def ask_gemini_with_retry(prompt: str, max_retries: int = 3) -> str:
    delay = 5
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            if response and response.text:
                return response.text
            return "Пустой ответ от нейросети."
        except Exception as e:
            err_str = str(e)
            print(f"Ошибка Gemini (попытка {attempt + 1}/{max_retries}): {err_str}")
            
            # Ловим лимиты (429), перегрузку (503) или квоты
            if "429" in err_str or "503" in err_str or "RESOURCE_EXHAUSTED" in err_str or "UNAVAILABLE" in err_str:
                if attempt == max_retries - 1:
                    return "⚠️ Нейросеть перегружена или исчерпан лимит. Пожалуйста, подождите минутку и повторите попытку."
                print(f"Сервер занят. Ждем {delay} сек...")
                time.sleep(delay)
                delay *= 2
            else:
                return "⚠️ Произошла временная ошибка при обращении к нейросети."
                
    return "Не удалось получить ответ от нейросети."

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    print(f"RECV DATA: {data}")

    try:
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            user_message = data["message"]["text"]
            
            print(f"User said: {user_message}")

            # Запрос к Gemini с надежной защитой
            ai_reply = ask_gemini_with_retry(user_message)
            print(f"Gemini reply: {ai_reply}")

            # Отправка ответа в Telegram
            async with httpx.AsyncClient() as httpx_client:
                payload = {
                    "chat_id": chat_id,
                    "text": ai_reply
                }
                tg_resp = await httpx_client.post(f"{TELEGRAM_API_URL}/sendMessage", json.dumps(payload), headers={"Content-Type": "application/json"})
                print(f"Telegram response: {tg_resp.text}")

    except Exception as e:
        print(f"Error handling webhook: {e}")

    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "Bot is running!"}
   
