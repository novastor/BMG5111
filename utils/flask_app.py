import os
import sys
import csv
import io
import subprocess
import logging
from io import BytesIO

import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydub import AudioSegment

# Import your processing functions
from stateful_scheduling import search_with_rag as rag
from realtime_whisper import audio_processing as ts
from main import do_optimization as opt

# Global variable to store transcription for testing only
g_ts = None
index = 'scheduler-vectorised'

app = FastAPI()
sys.dont_write_bytecode = True
logging.basicConfig(level=logging.INFO)

# CORS Middleware – Allow requests from any frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this for production by specifying your frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model for /optimize (if you later want to pass transcription via payload)
class TranscriptionRequest(BaseModel):
    transcription: str

# Response model for /optimize
class ScheduleEntry(BaseModel):
    scan_id: str
    scan_type: str
    duration: int
    priority: int
    patient_id: str
    start_time: str  # e.g., "YYYY-MM-DD HH:MM:SS"
    machine: str

class OptimizeResponse(BaseModel):
    schedule: list[ScheduleEntry]

@app.get("/")
def home():
    """Health check route."""
    return {"message": "FastAPI is running on Heroku/Render!"}

@app.get("/ffmpeg_version")
def ffmpeg_version():
    """Endpoint to check FFmpeg installation."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, check=True
        )
        version_info = result.stdout.splitlines()[0]
        return {"ffmpeg_version": version_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg check failed: {e}")

@app.post("/record")
def record_and_transcribe(file: UploadFile = File(...)):
    audio_data =  file.read()
    if not audio_data:
        raise HTTPException(status_code=400, detail="No audio data received")

    try:
        dat = io.BytesIO()
        dat.write(audio_data)
        dat.seek(0)
        # Pass the audio file directly to Whisper API
        transcript = ts(dat, file.filename)
        global g_ts
        g_ts = transcript
        return {"transcription": transcript}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

@app.post("/process")
def process_transcription():
    """
    Process the recorded transcription using RAG.
    Uses the transcript stored by /record.
    """
    global g_ts
    if not g_ts:
        raise HTTPException(status_code=400, detail="No recorded transcript found")
    result = rag(index, g_ts)
    return {"result": result}

@app.post("/optimize")
def optimize_workflow():
    """
    Optimize the workflow based on the recorded transcription.
    Uses the stored transcript rather than a hardcoded fake.
    """
    global g_ts
    if not g_ts:
        raise HTTPException(status_code=400, detail="No recorded transcript found")

    transcription = g_ts
    logging.info(f"Received transcription for optimization: {transcription}")
    
    # Process the transcription using RAG (returns CSV string)
    processed_csv = rag(index, transcription)
    if not processed_csv:
        raise HTTPException(status_code=400, detail="Processing failed")

    logging.info(f"Processed CSV Output:\n{processed_csv}")

    # Convert CSV string to list of dictionaries.
    try:
        csv_reader = csv.DictReader(io.StringIO(processed_csv))
        processed_output = list(csv_reader)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting CSV: {e}")

    # Optimize the workflow using opt()
    optimized_csv = opt(processed_output)
    if isinstance(optimized_csv, str):
        try:
            csv_reader = csv.DictReader(io.StringIO(optimized_csv))
            optimized_schedule = list(csv_reader)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error converting optimized CSV: {e}")
    else:
        optimized_schedule = optimized_csv

    # Format the output schedule.
    try:
        formatted_schedule = [
            {
                "scan_id": entry["scan_id"],
                "scan_type": entry["scan_type"],
                "duration": int(entry["duration"]),
                "priority": int(entry["priority"]),
                "patient_id": int(entry["patient_id"]),
                "start_time": entry.get("start_time", ""),
                "machine": entry.get("machine", entry["scan_type"]),
            }
            for entry in optimized_schedule
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error formatting schedule: {e}")

    logging.info(f"Optimized schedule: {formatted_schedule}")
    return {"schedule": formatted_schedule}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Default to 10000 if PORT is not set
    uvicorn.run(app, host="0.0.0.0", port=port)
