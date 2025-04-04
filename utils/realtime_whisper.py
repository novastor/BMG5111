
from openai import OpenAI
import wave
import io
import soundcard as sc
import numpy as np
from dotenv import load_dotenv
import os
'''
this block is no longer is use, as the deployment is working with a pre-recorded input for the time being
'''
def audio_capture():
    mic = sc.default_microphone()
#    print(mic)
    rate = 32000
    seconds = 10
    frames = rate*seconds
    data = mic.record(samplerate=rate,numframes=frames)
    d16 = np.int16(data*32767)
    wav_buffer = io.BytesIO()
#
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(32000)
        wf.writeframes(d16.tobytes())
    wav_buffer.name = "buffer.wav"
  # Reset buffer position
    wav_buffer = convert_bytearray_to_wav_ndarray(wav_buffer)
    return wav_buffer
def audio_mockup():
    '''
    this is a method used to run during demos, as the web hosting seems to break when trying to run pulseaudio(known issue?)
    '''
    mockup = io.BytesIO()
    mockup.write("the patient suffered an acute stroke with no further complications")
    mockup.seek(0)
    return mockup
def audio_processing():
        """
        transcribes audio file using whisper-1, returns string with detected speech
        note: currently, as we are passign it a pre-existing string, this will always return the same thing, but if run locally will work properly
        """
        buffer = audio_mockup()
        print(buffer)
        # Check if the API key is provided as an environment variable
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = input("Enter your OpenAI API key: ")

        # Initialize OpenAI client with the provided API key
        client = OpenAI(api_key=api_key)

        # Open the audio file in binary read mode
        transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=buffer,response_format='text',language='en'
            )
        print(transcript)
        print("recording complete")
        return transcript
