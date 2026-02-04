from fastapi import FastAPI, UploadFile, File, Form
import uuid
import os
import subprocess
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

VOICE_MODEL  = "/app/models/voices/en_US-amy-medium.onnx"
VOICE_CONFIG = "/app/models/voices/en_US-amy-medium.onnx.json"

@app.get("/")
async def health():
    return {"status": "TTS service running"}

@app.post("/tts")
async def tts(text: str = Form(...)):
    output_fname = f"/tmp/{uuid.uuid4().hex}.wav"

    # Validate model files exist
    if not os.path.isfile(VOICE_MODEL):
        return JSONResponse({"error": f"Model file not found: {VOICE_MODEL}"}, status_code=500)
    if not os.path.isfile(VOICE_CONFIG):
        return JSONResponse({"error": f"Config file not found: {VOICE_CONFIG}"}, status_code=500)

    cmd = [
        "piper",
        "--model", VOICE_MODEL,
        "--config", VOICE_CONFIG,
        "--output_file", output_fname,
    ]
    proc = subprocess.run(cmd, input=text.encode("utf-8"), check=True)
    return FileResponse(output_fname, media_type="audio/wav", filename="output.wav")

@app.post("/tts_metadata")
async def tts_metadata(text: str = Form(...)):
    output_fname = f"/tmp/{uuid.uuid4().hex}.wav"
    cmd = [
        "piper",
        "--model", VOICE_MODEL,
        "--config", VOICE_CONFIG,
        "--output_file", output_fname,
    ]
    subprocess.run(cmd, input=text.encode("utf-8"), check=True)
    return JSONResponse({"text": text, "wav_file": output_fname})
