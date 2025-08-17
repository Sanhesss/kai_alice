from fastapi import FastAPI, Request
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

@app.get("/")
async def health():
    return {"ok": True}

@app.post("/alice")
async def handle(request: Request):
    body = await request.json()
    user_text = body['request']['original_utterance']
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_text}]
    )
    reply = resp['choices'][0]['message']['content'].strip()
    return {
        "response": {
            "text": reply,
            "tts": reply,
            "end_session": False
        },
        "version": body["version"]
    }
