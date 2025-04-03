import csv 
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
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
pc_key  =  os.getenv("PINECONE_API_KEY")
print(pc_key)
index = 'scheduler-vectorised'
sys.dont_write_bytecode = True 
transcription =  "the patient suffered an acute stroke with no further complications"
processed_csv = rag(index, transcription,pc_key=pc_key)

 #csv_reader = csv.DictReader(io.StringIO(processed_csv))
processed_output = (processed_csv)
print(type(processed_output))
print(processed_output)