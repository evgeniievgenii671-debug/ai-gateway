
import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx

app = FastAPI()

# Получаем ключи из переменных окружения Render
API_KEYS = {
    "gemini": os.getenv("GEMINI_API_KEY"),
    "groq": os.getenv("GROQ_API_KEY"),
    "mistral": os.getenv("MISTRAL_API_KEY"),
    "backup": os.getenv("BACKUP_API_KEY")
}

class ChatRequest(BaseModel):
    message: str

async def call_gemini(prompt: str, api_key: str):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Gemini rate limit or error")
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

async def call_groq(prompt: str, api_key: str):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Groq rate limit or error")
        data = response.json()
        return data["choices"][0]["message"]["content"]

async def call_mistral(prompt: str, api_key: str):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "mistral-tiny",
        "messages": [{"role": "user", "content": prompt}]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Mistral rate limit or error")
        data = response.json()
        return data["choices"][0]["message"]["content"]

@app.post("/webhook")
async def ai_gateway(req: ChatRequest):
    prompt = req.message
    
    # 1. Попытка: Gemini
    if API_KEYS["gemini"]:
        try:
            answer = await call_gemini(prompt, API_KEYS["gemini"])
            return {"provider": "gemini", "response": answer}
        except Exception:
            pass

    # 2. Попытка: Groq
    if API_KEYS["groq"]:
        try:
            answer = await call_groq(prompt, API_KEYS["groq"])
            return {"provider": "groq", "response": answer}
        except Exception:
            pass

    # 3. Попытка: Mistral
    if API_KEYS["mistral"]:
        try:
            answer = await call_mistral(prompt, API_KEYS["mistral"])
            return {"provider": "mistral", "response": answer}
        except Exception:
            pass

    # 4. Попытка: Резервный провайдер
    if API_KEYS["backup"]:
        try:
            answer = await call_groq(prompt, API_KEYS["backup"]) 
            return {"provider": "backup", "response": answer}
        except Exception:
            pass

    raise HTTPException(status_code=503, detail="All AI providers are currently rate-limited or unavailable.")