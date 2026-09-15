import os
import logging
import httpx
from fastapi import FastAPI, Request, Response

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else ""
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

@app.get("/")
async def root():
    return {"status": "online", "service": "voice-ai-gateway"}

async def get_ai_response(prompt: str) -> str:
    """Генерация текстового ответа от ИИ-консультанта с защитой от сбоев"""
    system_prompt = (
        "Ты — профессиональный AI-менеджер компании по продаже строительных материалов, "
        "плитки и эпоксидных полов. Отвечай вежливо, коротко и по делу, помогая клиенту."
    )
    
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key is missing or empty.")
        return "Извините, сервис временно недоступен (не настроен ключ ИИ)."

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                },
                timeout=20.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
            
            logger.error(f"OpenAI API error status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"OpenAI Chat API error exception: {e}")

    # Резервная заглушка только на случай критического сбоя сети OpenAI
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

            # Получаем ответ от OpenAI
            ai_reply = await get_ai_response(user_text)

            # Безопасная отправка ответа обратно в Telegram без ошибок разметки (без parse_mode)
            if TELEGRAM_API_URL:
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
