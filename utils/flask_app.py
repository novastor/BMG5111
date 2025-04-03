from fastapi.middleware.cors import CORSMiddleware
from stateful_scheduling import search_with_rag as rag
from realtime_whisper import audio_processing as ts
from main import do_optimization as opt
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import io
import csv
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

@app.post("/optimize")
def mock_optimize():
    """Mock endpoint for testing frontend routing"""
    logging.info("Mock /optimize endpoint hit")

    # Mocked CSV response parsed into structured JSON
    mock_response = {
        "schedule": [
            {
                "scan_id": "S2",
                "scan_type": "MRI",
                "duration": 26,
                "priority": 1,
                "patient_id": 6,
                "start_time": "2025-03-25 11:11",
                "machine": "MRI"
            },
            {
                "scan_id": "S5",
                "scan_type": "CT",
                "duration": 35,
                "priority": 2,
                "patient_id": 8,
                "start_time": "2025-03-25 14:30",
                "machine": "CT"
            }
        ]
    }

    logging.info(f"Mock response: {mock_response}")
    return mock_response


# Run the FastAPI app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Default to 10000 if PORT is not set
    uvicorn.run(app, host="0.0.0.0", port=port)
