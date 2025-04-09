from openai import OpenAI
import wave
import io
#import soundcard as sc
import numpy as np
from dotenv import load_dotenv
import os

def audio_mockup():
    """
    This is a method used to run during demos.
    """
    mockup = io.BytesIO()
    mockup.write(b"the patient suffered an acute stroke with no further complications")
    mockup.seek(0)
    return mockup

def audio_processing(file_buffer, filename="audio.webm"):
    """
    Transcribes an audio file using whisper-1 and returns the detected text.
    Now supports multiple file types based on the filename extension.
    """
    # Reset the file buffer so we read from the beginning.
    file_buffer.seek(0)
    
    # Load environment variables and get the API key.
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = input("Enter your OpenAI API key: ")

    # Initialize OpenAI client with the provided API key.
    client = OpenAI(api_key=api_key)

    # Determine the MIME type based on the file extension.
    if filename.lower().endswith(".ogg"):
        mime_type = "audio/ogg"
    elif filename.lower().endswith(".wav"):
        mime_type = "audio/wav"
    else:
        mime_type = "audio/webm"

    # Create transcription using the audio file.
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=(filename, file_buffer, mime_type)
    )
    
    print(transcript)
    print("Recording complete")
    return transcript
