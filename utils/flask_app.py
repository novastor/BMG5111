from fastapi.middleware.cors import CORSMiddleware
from stateful_scheduling import search_with_rag as rag
from realtime_whisper import audio_processing as ts
from main import do_optimization as opt
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sys
import uvicorn

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
def record_and_transcribe():
    """API endpoint to trigger recording and transcription."""
    transcription = ts()  
    return {"transcription": transcription}

@app.post("/process")
def schedule():
    """API endpoint to process transcription."""
    content = "the patient suffered an acute stroke with no further complications"
    result = rag(index, content)
    return {"result": result}

@app.post("/optimize", response_model=OptimizeResponse)
def optimize_workflow(request: TranscriptionRequest):
    """Optimize the workflow based on transcribed input."""
    try:
        logging.info(f"Received transcription: {request.transcription}")

        # Process the transcription (RAG returns a CSV string)
        processed_csv = rag(index, request.transcription)
        if not processed_csv:
            raise HTTPException(status_code=400, detail="Processing failed")

        logging.info(f"Processed CSV Output:\n{processed_csv}")

        # Convert CSV to structured format (list of dictionaries)
        csv_reader = csv.DictReader(io.StringIO(processed_csv))
        processed_output = list(csv_reader)

        # Optimize workflow
        optimized_schedule = opt(processed_output)
        if not isinstance(optimized_schedule, list):
            raise HTTPException(status_code=500, detail="Optimization failed")

        # Validate & format schedule output
        formatted_schedule = [
            {
                "scan_id": entry["scan_id"],
                "scan_type": entry["scan_type"],
                "duration": entry["duration"],
                "priority": entry["priority"],
                "patient_id": entry["patient_id"],
                "start_time": entry.get("start_time", ""),  # Handle missing fields
                "machine": entry.get("machine", ""),
            }
            for entry in optimized_schedule
        ]

        logging.info(f"Optimized schedule: {formatted_schedule}")
        return {"schedule": formatted_schedule}

    except Exception as e:
        logging.error(f"Error in /optimize: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Run the FastAPI app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Default to 10000 if PORT is not set
    uvicorn.run(app, host="0.0.0.0", port=port)
