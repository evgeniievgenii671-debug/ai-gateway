import os
import logging
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
import httpx

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

class TelegramUpdate(BaseModel):
    update_id: int
    message: dict = None

@app.get("/")
async def root():
    return {"status": "online", "service": "multi-agent-gateway"}

async def process_message_logic(message: dict) -> str:
    """
    Единый диспетчер обработки сообщений: текст, голос и мультиагентная логика.
    """
    text = message.get("text")
    voice = message.get("voice")
    audio = message.get("audio")

    # 1. Обработка голосовых или аудио сообщений
    if voice or audio:
        file_id = voice.get("file_id") if voice else audio.get("file_id")
        logger.info(f"Received voice/audio file_id: {file_id}")
        # Здесь в будущем подключается распознавание через Whisper и озвучка через ElevenLabs
        return "🎙 Голосовое сообщение получено! Аудио-ассистент обрабатывает ваш запрос..."

    # 2. Обработка текстовых сообщений
    if text:
        system_prompt = (
            "Ты — главный AI-диспетчер и старший менеджер компании по продаже строительных материалов, "
            "плитки и эпоксидных полов. Ты координируешь мультиагентную систему, отвечаешь клиентам, "
            "помогаешь с выбором товаров и техническими вопросами."
        )

        if OPENAI_API_KEY and OPENAI_API_KEY != "your_key_here":
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": text}
                            ],
                            "temperature": 0.7
                        },
                        timeout=15.0
                    )
                    if response.status_code == 200:
                        res_data = response.json()
                        return res_data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"AI API error: {e}")

        # Автономный резервный ответ
        text_lower = text.lower()
        if "старт" in text_lower or "привет" in text_lower:
            return "Приветствую! Мультиагентный ассистент на связи. Чем могу помочь по плитке или эпоксидным полам?"
        elif "плитк" in text_lower:
            return "Каталог плитки готов к подбору. Какой объем или дизайн вас интересует?"
        elif "пол" in text_lower or "эпоксид" in text_lower:
            return "Эпоксидные покрытия — отличное решение. Подбираем материалы для заливки под ваш метраж."
        else:
            return f"Запрос принят мультиагентным диспетчером: «{text}». Обрабатываем информацию."

    return "Получено системное событие."

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Invalid JSON received: {e}")
        return Response(status_code=200)

    message = data.get("message")
    if not message:
        return Response(status_code=200)

    chat = message.get("chat", {})
    chat_id = chat.get("id")

    if not chat_id:
        return Response(status_code=200)

    # Жесткая защита типов chat_id от 400 ошибок
    try:
        safe_chat_id = int(chat_id)
    except (ValueError, TypeError):
        logger.error(f"Invalid chat_id format: {chat_id}")
        return Response(status_code=200)

    # Получаем ответ от логики ассистентов
    response_text = await process_message_logic(message)

    payload = {
        "chat_id": safe_chat_id,
        "text": response_text
    }

    async with httpx.AsyncClient() as client:
        try:
            tg_response = await client.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10.0)
            logger.info(f"TELEGRAM STATUS: {tg_response.status_code} | RESPONSE: {tg_response.text}")
        except Exception as e:
            logger.error(f"Failed to send message to Telegram: {e}")

    return Response(status_code=200)
