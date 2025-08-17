# main.py
from fastapi import FastAPI, Request
import os
from openai import OpenAI
import asyncio

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

@app.get("/")
async def health():
    return {"ok": True}

def ask_sync(prompt: str) -> str:
    # v1.x: client.chat.completions.create
    r = client.chat.completions.create(
        model="gpt-4o-mini",   # можно gpt-4o, gpt-4o-mini, gpt-4.1-mini и т.п.
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return r.choices[0].message.content.strip()

@app.post("/alice")
async def handle(request: Request):
    body = await request.json()
    utter = (body.get("request", {}).get("original_utterance")
             or body.get("request", {}).get("command")
             or "").strip()

    try:
        # потому что клиент синхронный — гоняем в thread + ограничим по времени
        reply = await asyncio.wait_for(asyncio.to_thread(ask_sync, utter), timeout=1.8)
    except asyncio.TimeoutError:
        reply = "Подумал... давай продолжим, я подключусь 🙂"
    except Exception:
        reply = "Пока не получилось обратиться к модели, но я на связи."

    return {
        "version": body.get("version", "1.0"),
        "response": {"text": reply, "tts": reply, "end_session": False}
    }
