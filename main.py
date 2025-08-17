# main.py
import os
import asyncio
from fastapi import FastAPI, Request
from openai import OpenAI

# ------------- инициализация OpenAI -------------
api_key = os.getenv("OPENAI_API_KEY")
print("ENV OPENAI_API_KEY exists:", bool(api_key), flush=True)
client = OpenAI(api_key=api_key)

app = FastAPI()


# ------------- health & debug -------------
@app.get("/")
async def health():
    return {"ok": True}

@app.get("/debug-openai")
async def debug_openai():
    """Простая проверка соединения с OpenAI (без Алисы)."""
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты проверочный бот."},
                {"role": "user", "content": "Скажи слово ПИНГ."},
            ],
            temperature=0.0,
        )
        txt = r.choices[0].message.content.strip()
        return {"ok": True, "reply": txt}
    except Exception as e:
        return {"ok": False, "error": repr(e)}


# ------------- синхронный вызов GPT -------------
def ask_gpt_sync(prompt: str) -> str:
    system = "Ты дружелюбный русскоязычный ассистент по имени Кай. Отвечай кратко и по делу."
    r = client.chat.completions.create(
        model="gpt-4o-mini",  # быстрый и дешёвый
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return r.choices[0].message.content.strip()


# ------------- обработчик Алисы -------------
@app.post("/alice")
async def alice_handle(request: Request):
    body = await request.json()
    print("ALICE BODY:", body, flush=True)

    req = (body.get("request") or {})
    user_text = (req.get("original_utterance") or req.get("command") or "").strip()

    # запасной вариант — собрать текст из nlu.tokens
    if not user_text:
        nlu = (req.get("nlu") or {})
        tokens = nlu.get("tokens") or []
        if tokens:
            user_text = " ".join(tokens).strip()

    print("USER_TEXT:", repr(user_text), flush=True)

    # выход
    if user_text.lower() in {"выход", "стоп", "хватит"}:
        reply = "До связи! Зови, если что."
        return {
            "version": body.get("version", "1.0"),
            "response": {"text": reply, "tts": reply, "end_session": True},
        }

    # пусто — приветствие
    if not user_text:
        reply = "Привет! Я Кай. Спроси меня о чём угодно."
        return {
            "version": body.get("version", "1.0"),
            "response": {"text": reply, "tts": reply, "end_session": False},
        }

    # вызов GPT с понятным логом
    try:
        # Яндекс даёт ~3–3.5 с. Ставим 3.0 — баланс скорости и стабильности
        reply = await asyncio.wait_for(
            asyncio.to_thread(ask_gpt_sync, user_text),
            timeout=3.0
        )
    except asyncio.TimeoutError:
        print("OPENAI TIMEOUT", flush=True)
        reply = "Подумал... давай продолжим, я подключусь 😉"
    except Exception as e:
        print("OPENAI ERROR:", repr(e), flush=True)
        reply = f"Пока не получилось обратиться к модели. Ты написал: «{user_text}»."

    return {
        "version": body.get("version", "1.0"),
        "response": {"text": reply, "tts": reply, "end_session": False},
    }
