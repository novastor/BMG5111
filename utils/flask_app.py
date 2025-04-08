from fastapi.middleware.cors import CORSMiddleware
from fastapi import  FastAPI, UploadFile, File
from stateful_scheduling import search_with_rag as rag
from realtime_whisper import audio_processing as ts
from main import do_optimization as opt
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import io
from io import BytesIO
import csv
import sys
import uvicorn
from pydub import AudioSegment
g_ts = None
# Global variables
index = 'scheduler-vectorised'
app = FastAPI()
sys.dont_write_bytecode = True 
logging.basicConfig(level=logging.INFO)

# CORS Middleware (Allow requests from any frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Model for /optimize
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
    """API endpoint to trigger recording and transcription."""
    audio_data =  file.read()

    # Convert audio data into a buffer (in-memory)
    audio_buffer = BytesIO(audio_data)

    # If the audio format is webm (or any other type), use pydub to convert it to a WAV file
    # Assuming the input is in "audio/webm" format (can be changed depending on actual format)
    audio = AudioSegment.from_file(audio_buffer, format="webm")

    # Now audio is an AudioSegment object; you can process it further
    # For example, convert it to WAV
    wav_buffer = BytesIO()
    audio.export(wav_buffer, format="wav")

    # You can now use the wav_buffer as a file object (it’s in-memory)
    wav_buffer.seek(0)  # Rewind the buffer to the beginning
    transcription = ts(wav_buffer)  
    g_ts = transcription
    return {"transcription": transcription}

@app.post("/process")
def schedule():
    """API endpoint to process transcription."""
    content = "the patient suffered an acute stroke with no further complications"
    result = rag(index, content)
    return {"result": result}

@app.post("/optimize")
def optimize_workflow():
    """Optimize the workflow based on transcribed input."""
    try:
        transcription =  "the patient suffered an acute stroke with no further complications"
        transcription = g_ts
        print("transcription:")
        print(transcription)
        logging.info(f"Received transcription: {transcription}")
        
        # Process the transcription (RAG returns a CSV string)
        processed_csv = rag(index, transcription)
        if not processed_csv:
            raise HTTPException(status_code=400, detail="Processing failed")

        logging.info(f"Processed CSV Output:\n{processed_csv}")

        # Convert CSV string to list of dictionaries
        #csv_reader = csv.DictReader(io.StringIO(processed_csv))
        processed_output = (processed_csv)
        # Validate processed_output contains necessary keys
       #required_keys = {"scan_id", "scan_type", "duration", "priority", "patient_id", "check_in_date", "check_in_time"}
       #for entry in processed_output:
       #    if not required_keys.issubset(entry.keys()):
       #        raise HTTPException(status_code=400, detail="Missing required fields in CSV data")

        # Optimize workflow (assuming opt() is a function that processes this list)
        optimized_csv = opt(processed_output)

        # Check if the result is a CSV string (which is expected if .to_csv() is used)
        if isinstance(optimized_csv, str):
            # Convert the CSV string back into a list of dictionaries
            csv_reader = csv.DictReader(io.StringIO(optimized_csv))
            optimized_schedule = (csv_reader)
        else:
            # If it's not a CSV string, treat it as a list directly
            optimized_schedule = optimized_csv
        print("i did it")

        # Validate & format schedule output
        formatted_schedule = [
            {
                "scan_id": entry["scan_id"],
                "scan_type": entry["scan_type"],
                "duration": int(entry["duration"]),  # Convert to integer
                "priority": int(entry["priority"]),  # Convert to integer
                "patient_id": int(entry["patient_id"]),  # Convert to integer
                "start_time": entry.get("start_time", ""),  # Default empty if missing
                "machine": entry.get("machine", entry["scan_type"]),  # Assume machine is scan_type if missing
            }
            for entry in optimized_schedule
        ]
        print("formatted")
        logging.info(f"Optimized schedule: {formatted_schedule}")
        return {"schedule": formatted_schedule}

    except Exception as e:
        logging.error(f"Error in /optimize: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Run the FastAPI app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Default to 10000 if PORT is not set
    uvicorn.run(app, host="0.0.0.0", port=port)
