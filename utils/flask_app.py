
from fastapi.middleware.cors import CORSMiddleware
from stateful_scheduling import search_with_rag as rag
from realtime_whisper  import audio_processing as ts
from main import do_optimization as opt
import datetime
import logging
from fastapi import FastAPI,HTTPException
import os
import sys
import uvicorn
import requests
index ='scheduler-vectorised'
transcription = ''
result = ''
current_schedule = ''
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

link = os.environ.get('api_link')
@app.get("/")
def home():
    return {"message": "FastAPI is running on Heroku/Render!"}


@app.post("/record")
async def record_and_transcribe():
    """API endpoint to trigger recording and transcription."""
    transcription = ts()  
    return {"transcription": transcription}

@app.post('/process')

async def schedule():
    """API endpoint to trigger recording and transcription."""
    content = "the patient suffered an acute stroke with no further complications"
    result = rag(index,content)

    return {"result": result}



@app.post("/optimize")
async def optimize_workflow(transcription: str):
    """Optimizes schedule using transcription without external process call."""
    try:
        # Directly process the transcription instead of making an external request
        processed_result = rag("scheduler-vectorised", transcription)
        if not processed_result or "answer" not in processed_result:
            raise HTTPException(status_code=400, detail="Processing failed")

        # Extract processed output
        processed_output = processed_result["answer"]

        # Optimize
        optimized_schedule = opt(processed_output)

        return {"schedule": optimized_schedule}

    except Exception as e:
        return {"error": str(e)}
    
    except Exception as e:
        logging.error(f"Error calling /process: {e}")
        raise HTTPException(status_code=500, detail=str(e))

##this is the scheduler for handling recordings, need to swap this in once testing is done
#def schedule(content):
#    """API endpoint to trigger recording and transcription."""
#    print(content)
#    result = rag(index,content)  # Call your script
#    result = result["answer"]
#    print("\nTranscription:")
#    print(result)
#    return jsonify({"result": result})
      
if __name__ == '__main__':
       port = int(os.environ.get("PORT", 10000))  # Default to 5000 if PORT is not set
       uvicorn.run(app, host="0.0.0.0", port=port)    
    
   