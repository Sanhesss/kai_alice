# main.py
import os
import asyncio
from fastapi import FastAPI, Request
from openai import OpenAI

# Инициализируем OpenAI из переменной окружения
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# Health-check: Render/брaузер проверяет, что сервис жив
@app.get("/")
async def health():
    return {"ok": True}

def ask_gpt_sync(prompt: str) -> str:
    """Синхронный вызов GPT (оборачиваем в thread, чтобы не блокировать event loop)."""
    system = "Ты дружелюбный русскоязычный ассистент по имени Кай. Отвечай кратко и по делу."
    r = client.chat.completions.create(
        model="gpt-4o-mini",  # можно заменить на gpt-4o, gpt-4.1-mini и т.д. если доступны
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return r.choices[0].message.content.strip()

@app.post("/alice")
async def alice_handle(request: Request):
    body = await request.json()

    # Достаём текст от пользователя (Алиса присылает и command, и original_utterance)
    req = body.get("request", {}) or {}
    user_text = (req.get("original_utterance") or req.get("command") or "").strip().lower()

    # Примитивные команды выхода
    if user_text in {"выход", "стоп", "хватит"}:
        reply = "До связи! Зови, если что."
        return {
            "version": body.get("version", "1.0"),
            "response": {"text": reply, "tts": reply, "end_session": True},
        }

    # Если ничего не сказано — поздороваемся
    if not user_text:
        reply = "Привет! Я Кай. Спроси меня о чём угодно."
        return {
            "version": body.get("version", "1.0"),
            "response": {"text": reply, "tts": reply, "end_session": False},
        }

    # Вызываем модель, но не даём ей зависнуть дольше ~2 секунд
    try:
        reply = await asyncio.wait_for(asyncio.to_thread(ask_gpt_sync, user_text), timeout=1.8)
    except asyncio.TimeoutError:
        reply = "Подумал... давай продолжим, я подключусь 😉"
    except Exception:
        reply = "Пока не получилось обратиться к модели, но я на связи."

    return {
        "version": body.get("version", "1.0"),
        "response": {"text": reply, "tts": reply, "end_session": False},
    }
