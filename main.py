import os
from fastapi import FastAPI, Request
import google.generativeai as genai
import requests

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


@app.get("/")
def home():
  return {"status": "running"}


@app.post("/")
async def webhook(request: Request):
  data = await request.json()

  if "message" in data and "text" in data["message"]:
    chat_id = data["message"]["chat"]["id"]
    user_text = data["message"]["text"]

    try:
      response = model.generate_content(user_text)
      ai_reply = response.text
    except Exception as e:
      ai_reply = f"Ошибка Gemini API: {e}"

    payload = {"chat_id": chat_id, "text": ai_reply}
    requests.post(TELEGRAM_API_URL, json=payload)

  return {"ok": True}
   
                  
