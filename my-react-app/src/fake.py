import requests
from pydub import AudioSegment
import io

# Generate a sine wave as a test input
def generate_test_audio():
    duration_ms = 5000  # 5 seconds
    frequency = 440  # A4 note (440 Hz)
    
    # Create sine wave at 440 Hz for 5 seconds
    sine_wave = AudioSegment.sine(frequency=frequency, duration=duration_ms)
    
    # Export the sine wave to an in-memory file (like a "webm" format)
    audio_buffer = io.BytesIO()
    sine_wave.export(audio_buffer, format="webm")
    audio_buffer.seek(0)  # Rewind the buffer to the start
    return audio_buffer

# Upload the generated fake audio to your FastAPI backend
def upload_fake_audio(api_url):
    try:
        # Generate the fake audio file (sine wave)
        audio_file = generate_test_audio()
        
        # Prepare the form data
        files = {'file': ('fake_audio.webm', audio_file, 'audio/webm')}
        
        # Send the file to the backend for transcription
        response = requests.post(f"{api_url}/record", files=files)
        
        if response.status_code == 200:
            print("Transcription result:", response.json())
        else:
            print(f"Failed to upload audio. Status code: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error uploading fake audio: {str(e)}")

# Replace with your FastAPI backend URL
API_BASE_URL = "https://bmg5111-1.onrender.com/"  # Modify this with your actual URL

# Test the script by uploading the fake audio
upload_fake_audio(API_BASE_URL)
