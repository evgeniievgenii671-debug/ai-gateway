import os
import logging
import httpx
from fastapi import FastAPI, Request, Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M").strip()
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "").strip()

@app.get("/")
async def root():
    return {"status": "online", "service": "voice-ai-gateway"}

async def get_ai_response(prompt: str) -> str:
    system_prompt = (
        "Ты — профессиональный AI-менеджер компании по продаже строительных материалов, "
        "плитки и эпоксидных полов. Отвечай вежливо, коротко и по делу, помогая клиенту."
    )
    
    async with httpx.AsyncClient() as client:
        # 1. Пробуем Groq с актуальной бесплатной моделью
        if GROQ_API_KEY:
            try:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7
                    },
                    timeout=15.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and data["choices"]:
                        return data["choices"][0]["message"]["content"]
                logger.warning(f"Groq failed with status {response.status_code}: {response.text}")
            except Exception as e:
                logger.warning(f"Groq exception: {e}")

        # 2. Если Groq недоступен — переходим на Gemini
        if GEMINI_API_KEY:
            try:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
                    json={
                        "contents": [
                            {"role": "user", "parts": [{"text": f"{system_prompt}\n\nВопрос клиента: {prompt}"}]}
                        ]
                    },
                    timeout=15.0
                )
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                logger.warning(f"Gemini failed with status {response.status_code}")
            except Exception as e:
                logger.warning(f"Gemini exception: {e}")

        # 3. Запасной вариант — Mistral
        if MISTRAL_API_KEY:
            try:
                response = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
                    json={
                        "model": "mistral-small-latest",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7
                    },
                    timeout=15.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and data["choices"]:
                        return data["choices"][0]["message"]["content"]
                logger.warning(f"Mistral failed with status {response.status_code}")
            except Exception as e:
                logger.warning(f"Mistral exception: {e}")

    # Финальная текстовая заглушка, если все три сервиса недоступны
    text_lower = prompt.lower()
    if "плитк" in text_lower:
        return "У нас отличный ассортимент плитки. Какой стиль или объем вас интересует?"
    elif "пол" in text_lower or "эпоксид" in text_lower:
        return "Эпоксидные полы — прочное решение. Делаете для жилого или коммерческого помещения?"
    else:
        return f"Ваш запрос принят. Менеджер свяжется с вами для уточнения деталей."

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"TELEGRAM INCOMING: {data}")

        if "message" in data and "text" in data["message"]:
            chat_id = int(data["message"]["chat"]["id"])
            user_text = data["message"]["text"]

            ai_reply = await get_ai_response(user_text)

            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{TELEGRAM_API_URL}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": ai_reply
                    },
                    timeout=10.0
                )

        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return Response(status_code=200)
