from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import whisper
import tempfile
import os

app = FastAPI()

# Load Whisper model (tiny for speed)
print("Loading Whisper model...")
model = whisper.load_model("tiny")
print("Whisper model loaded!")

@app.get("/")
async def health():
    return {"status": "ASR service running"}

@app.post("/asr")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio file to text using Whisper
    Accepts: WAV, MP3, OGG, etc.
    Returns: {"text": "transcribed text"}
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1]) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Transcribe
        result = model.transcribe(tmp_path)
        
        # Clean up
        os.unlink(tmp_path)
        
        return JSONResponse({
            "text": result["text"].strip(),
            "language": result.get("language", "unknown")
        })
    
    except Exception as e:
        return JSONResponse(
            {"error": f"Transcription failed: {str(e)}"},
            status_code=500
        )
