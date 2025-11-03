from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from gtts import gTTS
import os, uuid

app = FastAPI()

# Supported languages and voices
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "hi": "Hindi",
    "ja": "Japanese"
}

SUPPORTED_VOICES = ["male", "female"]

@app.get("/")
def home():
    return {"message": "Chatterbox Voice API is running", "supported_languages": SUPPORTED_LANGUAGES}

@app.post("/v1/generate")
async def generate_voice(req: Request):
    try:
        data = await req.json()
        text = data.get("text", "").strip()
        language = data.get("language", "en").lower()
        voice = data.get("voice", "female").lower()

        if not text:
            return JSONResponse({"error": "Missing 'text' parameter"}, status_code=400)

        # Validate language
        if language not in SUPPORTED_LANGUAGES:
            return JSONResponse({"error": f"Unsupported language '{language}'"}, status_code=400)

        # Validate voice
        if voice not in SUPPORTED_VOICES:
            voice = "female"  # fallback

        filename = f"audio_{uuid.uuid4()}.mp3"

        # Generate speech
        tts = gTTS(text=text, lang=language)
        tts.save(filename)

        audio_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{filename}"
        return {"audio_url": audio_url, "language": language, "voice": voice}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/{filename}")
async def serve_audio(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename)
    return JSONResponse({"error": "File not found"}, status_code=404)
