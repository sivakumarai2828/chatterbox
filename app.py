from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from gtts import gTTS
import os, uuid

app = FastAPI()

@app.post("/v1/generate")
async def generate_voice(req: Request):
    data = await req.json()
    text = data.get("text", "Hello from Chatterbox!")
    lang = data.get("language", "en")
    filename = f"audio_{uuid.uuid4()}.mp3"
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    return {"audio_url": f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{filename}"}

@app.get("/{filename}")
async def serve_audio(filename: str):
    return FileResponse(filename)
