
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
    allow_origins=["*"],  # Change this to specific frontend URLs for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

link = os.environ.get('api_link')
@app.get("/")  
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
async def optimizer():
    #logging.info(f"API link from environment: {link}")
    """API endpoint to trigger optimization."""
    if not link:
        raise HTTPException(status_code=500, detail="API link not found in environment variables")

    target = f"https://your-app.onrender.com/process"
    logging.info(f"Constructed target URL: {target}")
    response = requests.post(target)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get result from /process")
    
    result = response.json().get("result")
    if not result:
        raise HTTPException(status_code=400, detail="No result from /process")

    optimized_result = opt(result)
    return {"schedule": optimized_result}


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
    
   