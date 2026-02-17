"""
Whisper Transcription API
- Accepts an Archive.org URL
- Downloads audio using yt-dlp
- Transcribes using Whisper Large v3 on GPU
- Returns the transcription text
- Cleans up all temporary files after processing
"""

import sys
print("----------------------------------------------------------------", flush=True)
print("APPLICATION STARTUP BEGINNING...", flush=True)
print("Importing modules...", flush=True)

import os
import uuid
import shutil
import whisper
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import torch

# --- App Setup ---
app = FastAPI(
    title="Whisper Transcription API",
    description="Transcribe audio/video from Archive.org using OpenAI Whisper Large v3",
    version="1.0.0",
)

# --- Load Model Once at Startup ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[INFO] Loading Whisper large-v3 on device: {DEVICE}")
model = whisper.load_model("large-v3", device=DEVICE)
print("[INFO] Model loaded successfully!")


# --- Request Schema ---
class TranscribeRequest(BaseModel):
    url: str  # Archive.org URL


# --- Health Check ---
@app.get("/")
async def health_check():
    return {
        "status": "running",
        "model": "whisper-large-v3",
        "device": DEVICE,
        "gpu_available": torch.cuda.is_available(),
    }


# --- Main Transcription Endpoint ---
@app.post("/transcribe")
async def transcribe(request: TranscribeRequest):
    """
    Accepts an Archive.org URL, downloads the audio,
    transcribes it with Whisper, and returns the text.
    The downloaded file is deleted after transcription.
    """
    url = request.url
    job_id = str(uuid.uuid4())[:8]
    temp_dir = f"/tmp/whisper_jobs/{job_id}"

    try:
        # 1. Create temp directory
        os.makedirs(temp_dir, exist_ok=True)
        print(f"[{job_id}] Downloading audio from: {url}")

        # 2. Download audio using yt-dlp
        output_template = os.path.join(temp_dir, "audio.%(ext)s")
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "-x",                      # Extract audio only
            "--audio-format", "wav",    # Convert to WAV for Whisper
            "--audio-quality", "0",     # Best quality
            "-o", output_template,
            url,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 min timeout for download
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Download failed: {result.stderr[:500]}"
            )

        # 3. Find the downloaded audio file
        audio_file = None
        for f in os.listdir(temp_dir):
            if f.startswith("audio"):
                audio_file = os.path.join(temp_dir, f)
                break

        if not audio_file or not os.path.exists(audio_file):
            raise HTTPException(
                status_code=500,
                detail="Audio file not found after download."
            )

        file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
        print(f"[{job_id}] Audio downloaded: {audio_file} ({file_size_mb:.1f} MB)")

        # 4. Transcribe with Whisper
        print(f"[{job_id}] Starting transcription...")
        transcription = model.transcribe(
            audio_file,
            verbose=False,
        )

        text = transcription.get("text", "")
        language = transcription.get("language", "unknown")
        segments = transcription.get("segments", [])

        # Build segments with timestamps
        segments_data = []
        for seg in segments:
            segments_data.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
            })

        print(f"[{job_id}] Transcription complete! Language: {language}, Length: {len(text)} chars")

        # 5. Return the result
        return {
            "job_id": job_id,
            "url": url,
            "language": language,
            "text": text,
            "segments": segments_data,
            "audio_size_mb": round(file_size_mb, 2),
        }

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408,
            detail="Download timed out (>10 minutes)."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )
    finally:
        # 6. ALWAYS clean up - delete the downloaded files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"[{job_id}] Cleaned up temp files at {temp_dir}")
