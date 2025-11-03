from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from gtts import gTTS
import speech_recognition as sr
import os, uuid

app = FastAPI()

SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "hi": "Hindi",
    "ja": "Japanese"
}

@app.get("/")
def home():
    return {
        "message": "🎙️ Chatterbox Voice API running",
        "supported_languages": SUPPORTED_LANGUAGES,
        "endpoints": {
            "TTS": "/v1/tts",
            "STT": "/v1/stt",
            "Speech↔Speech": "/v1/speech2speech"
        }
    }

# ----------------------------
# TEXT → SPEECH
# ----------------------------
@app.post("/v1/tts")
async def text_to_speech(req: Request):
    try:
        data = await req.json()
        text = data.get("text", "").strip()
        lang = data.get("language", "en").lower()

        if not text:
            return JSONResponse({"error": "Missing text"}, status_code=400)
        if lang not in SUPPORTED_LANGUAGES:
            return JSONResponse({"error": f"Unsupported language: {lang}"}, status_code=400)

        filename = f"tts_{uuid.uuid4()}.mp3"
        gTTS(text=text, lang=lang).save(filename)

        audio_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{filename}"
        return {"audio_url": audio_url, "language": lang}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ----------------------------
# SPEECH → TEXT
# ----------------------------
@app.post("/v1/stt")
async def speech_to_text(file: UploadFile = File(...), language: str = Form("en")):
    try:
        if language not in SUPPORTED_LANGUAGES:
            return JSONResponse({"error": f"Unsupported language: {language}"}, status_code=400)

        filename = f"stt_{uuid.uuid4()}.wav"
        with open(filename, "wb") as f:
            f.write(await file.read())

        recognizer = sr.Recognizer()
        with sr.AudioFile(filename) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language=language)

        os.remove(filename)
        return {"text": text, "language": language}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ----------------------------
# SPEECH → SPEECH
# ----------------------------
@app.post("/v1/speech2speech")
async def speech_to_speech(
    file: UploadFile = File(...),
    source_language: str = Form("en"),
    target_language: str = Form("en")
):
    try:
        # Step 1: Speech → Text
        stt_filename = f"stt_{uuid.uuid4()}.wav"
        with open(stt_filename, "wb") as f:
            f.write(await file.read())

        recognizer = sr.Recognizer()
        with sr.AudioFile(stt_filename) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language=source_language)

        # Step 2: Text → Speech (Target Language)
        tts_filename = f"s2s_{uuid.uuid4()}.mp3"
        gTTS(text=text, lang=target_language).save(tts_filename)

        audio_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{tts_filename}"

        # Cleanup
        os.remove(stt_filename)
        return {"audio_url": audio_url, "source_text": text, "target_language": target_language}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/{filename}")
async def serve_audio(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename)
    return JSONResponse({"error": "File not found"}, status_code=404)
