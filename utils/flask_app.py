# app.py
from flask import Flask, jsonify
from flask_cors import CORS
from realtime_whisper  import audio_processing as ts
from stateful_scheduling import search_with_rag as rag
from main import do_optimization as opt
import datetime
import requests
index ='scheduler-vectorised'
transcription = ''
result = ''
current_schedule = ''
app = Flask(__name__)

CORS(app)  # Enable cross-origin requests for React frontend

@app.route('/record', methods=['POST'])
def record_and_transcribe():
    """API endpoint to trigger recording and transcription."""
    transcription = ts()  
    print("\nTranscription:")
    return jsonify({"transcription": transcription})


@app.route('/process', methods=['POST'])

def schedule():
    """API endpoint to trigger recording and transcription."""
    content = "the patient suffered an acute stroke with no further complications"
    result = rag(index,content)

    return jsonify({"result": result})


@app.route('/optimize', methods=['POST'])
def optimizer():
    """API endpoint to trigger optimization."""
    # Make a POST request to /process
    response = requests.post("http://localhost:5000/process")
    print("response = ")
    if response.status_code != 200:
        return jsonify({"error": "Failed to get result from /process"}), 400
    
    result = response.json().get("result")
    

    if not result:
        return jsonify({"error": "No result from /process"}), 400
    
    optimized_result = opt(result)
    print("\nSchedule:")
    print(optimized_result)
    return jsonify({"schedule": optimized_result})

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
    app.run(debug=False)
    
    
    