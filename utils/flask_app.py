from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from stateful_scheduling import search_with_rag as rag
from realtime_whisper import audio_processing as ts
from main import do_optimization as opt
import logging
from pydantic import BaseModel
import os
from io import BytesIO
import csv
import sys
import uvicorn
from pydub import AudioSegment

# Global variable to store recorded transcript (for testing only)
g_ts = None
index = 'scheduler-vectorised'

app = FastAPI()
sys.dont_write_bytecode = True
logging.basicConfig(level=logging.INFO)

# CORS Middleware (allow requests from any frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify with your frontend URL for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Model for /optimize (if you decide to send transcription in a payload)
class TranscriptionRequest(BaseModel):
    transcription: str

# Response Model for /optimize
class ScheduleEntry(BaseModel):
    scan_id: str
    scan_type: str
    duration: int
    priority: int
    patient_id: str
    start_time: str  # "YYYY-MM-DD HH:MM:SS"
    machine: str

class OptimizeResponse(BaseModel):
    schedule: list[ScheduleEntry]

@app.get("/")
def home():
    """Health check route."""
    return {"message": "FastAPI is running on Heroku/Render!"}

@app.post("/record")
def record_and_transcribe(file: UploadFile = File(...)):
    """API endpoint to receive the audio recording, convert it to WAV, transcribe it, and store the transcript."""
    # Read the uploaded audio data
    audio_data = file.read()
    if not audio_data:
        raise HTTPException(status_code=400, detail="No audio data received")

    print("Received audio data (first 100 bytes):", audio_data[:100])

    # Create a buffer for in-memory audio processing
    audio_buffer = BytesIO(audio_data)

    # Convert audio from WebM to WAV (adjust "webm" if needed)
    try:
        audio = AudioSegment.from_file(audio_buffer, format="webm")
        wav_buffer = BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)  # Reset buffer pointer
        logging.info("Audio conversion successful!")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing audio file: {e}")

    # Transcribe the WAV audio using the ts() function (ensure ts is working correctly)
    transcription = ts(wav_buffer)
    if transcription is None:
        raise HTTPException(status_code=500, detail="Transcription failed")

    # Store the transcript in a global variable for testing/demo purposes
    global g_ts
    g_ts = transcription

    logging.info("Got transcription: " + str(transcription))
    return {"transcription": transcription}

@app.post("/process")
def process_transcription():
    """
    API endpoint to process the recorded transcription using RAG.
    Uses the transcript stored by /record.
    """
    global g_ts
    if not g_ts:
        raise HTTPException(status_code=400, detail="No recorded transcript found")
    # Use the recorded transcript (g_ts) for processing
    result = rag(index, g_ts)
    return {"result": result}

@app.post("/optimize")
def optimize_workflow():
    """
    Optimize the workflow based on the recorded transcription.
    The recorded transcript (from /record) is used rather than a hardcoded fake.
    """
    global g_ts
    if not g_ts:
        raise HTTPException(status_code=400, detail="No recorded transcript found")

    transcription = g_ts
    logging.info(f"Received transcription: {transcription}")
    
    # Process the transcription using RAG, which returns a CSV string
    processed_csv = rag(index, transcription)
    if not processed_csv:
        raise HTTPException(status_code=400, detail="Processing failed")

    logging.info(f"Processed CSV Output:\n{processed_csv}")

    # Here, processed_csv is assumed to be a CSV string
    # Convert CSV string into a list of dictionaries
    try:
        csv_reader = csv.DictReader(BytesIO(processed_csv.encode('utf-8')).read().decode('utf-8').splitlines())
        optimized_schedule = list(csv_reader)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting CSV: {e}")

    # Optimize workflow using the opt() function
    optimized_csv = opt(optimized_schedule)
    if isinstance(optimized_csv, str):
        try:
            csv_reader = csv.DictReader(io.StringIO(optimized_csv))
            optimized_schedule = list(csv_reader)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error converting optimized CSV: {e}")
    else:
        optimized_schedule = optimized_csv

    # Validate and format the schedule for the response
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
