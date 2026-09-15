import os
import logging
import httpx
from fastapi import FastAPI, Request, Response

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8680814733:AAGUbD-eHtDXy7XyR4N2TpEQmdk0vYX_B8M")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

@app.get("/")
async def root():
    return {"status": "online", "service": "voice-ai-gateway"}

async def get_ai_response(prompt: str) -> str:
    """Генерация текстового ответа от ИИ-консультанта"""
    system_prompt = (
        "Ты — профессиональный AI-менеджер компании по продаже строительных материалов, "
        "плитки и эпоксидных полов. Отвечай вежливо, коротко и по делу, помогая клиенту с выбором."
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
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7
                    },
                    timeout=20.0
                )
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI Chat API error: {e}")

    # Резервная умная заглушка если ключ не задан
    text_lower = prompt.lower()
    if "плитк" in text_lower:
        return "У нас отличный ассортимент плитки. Какой стиль или объем вас интересует?"
    elif "пол" in text_lower or "эпоксид" in text_lower:
        return "Эпоксидные полы — прочное решение. Делаете для жилого или коммерческого помещения?"
    else:
        return f"Ваш запрос принят: «{prompt}». Менеджер свяжется с вами для уточнения деталей."

async def transcribe_audio_file(file_path: str) -> str:
    """Распознавание голосового сообщения через OpenAI Whisper"""
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_key_here":
        return "Голосовое сообщение получено (ИИ-ключ для расшифровки не настроен)."

    try:
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as audio_file:
                files = {"file": (os.path.basename(file_path), audio_file, "audio/ogg")}
                data = {"model": "whisper-1"}
                response = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    files=files,
                    data=data,
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json().get("text", "")
    except Exception as e:
        logger.error(f"Whisper API error: {e}")
    return "Не удалось распознать голосовое сообщение."

async def text_to_speech_audio(text: str, output_path: str) -> bool:
    """Озвучка текста через OpenAI TTS"""
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_key_here":
        return False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "tts-1",
                    "input": text,
                    "voice": "alloy"  # Доступные голоса: alloy, echo, fable, onyx, nova, shimmer
                },
                timeout=30.0
            )
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return True
    except Exception as e:
        logger.error(f"OpenAI TTS API error: {e}")
    return False

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Invalid JSON: {e}")
        return Response(status_code=200)

    message = data.get("message")
    if not message:
        return Response(status_code=200)

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return Response(status_code=200)

    try:
        safe_chat_id = int(chat_id)
    except (ValueError, TypeError):
        return Response(status_code=200)

    user_text = ""
    is_voice_request = False

    # 1. Проверяем, есть ли голосовое или аудио
    voice = message.get("voice") or message.get("audio")
    if voice:
        is_voice_request = True
        file_id = voice.get("file_id")
        
        async with httpx.AsyncClient() as client:
            # Получаем путь к файлу в Telegram
            file_info_resp = await client.get(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}")
            if file_info_resp.status_code == 200:
                file_path_tg = file_info_resp.json().get("result", {}).get("file_path")
                if file_path_tg:
                    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path_tg}"
                    audio_download = await client.get(download_url)
                    
                    local_audio = "temp_voice.ogg"
                    with open(local_audio, "wb") as f:
                        f.write(audio_download.content)
                    
                    # Переводим голос в текст
                    user_text = await transcribe_audio_file(local_audio)
                    
                    # Удаляем временный файл
                    if os.path.exists(local_audio):
                        os.remove(local_audio)
    else:
        # Обычный текст
        user_text = message.get("text", "")

    if not user_text:
        user_text = "Привет"

    # Получаем ответ от ИИ
    ai_response_text = await get_ai_response(user_text)

    async with httpx.AsyncClient() as client:
        # Если пользователь писал голосом, пробуем ответить тоже голосом
        sent_as_voice = False
        if is_voice_request:
            local_tts = "response_voice.mp3"
            if await text_to_speech_audio(ai_response_text, local_tts):
                with open(local_tts, "rb") as voice_file:
                    files = {"voice": (local_tts, voice_file, "audio/mpeg")}
                    data = {"chat_id": safe_chat_id, "caption": "🎙 Ответ ассистента"}
                    tg_resp = await client.post(f"{TELEGRAM_API_URL}/sendVoice", data=data, files=files, timeout=30.0)
                    if tg_resp.status_code == 200:
                        sent_as_voice = True
                if os.path.exists(local_tts):
                    os.remove(local_tts)

        # Если голосом отправить не вышло или запрос был текстовым — шлем текстом
        if not sent_as_voice:
            payload = {
                "chat_id": safe_chat_id,
                "text": ai_response_text
            }
            tg_resp = await client.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10.0)
            logger.info(f"TELEGRAM STATUS: {tg_resp.status_code} | RESPONSE: {tg_resp.text}")

    return Response(status_code=200)
