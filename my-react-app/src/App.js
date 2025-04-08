import React, { useState, useRef } from "react";
import { FaMicrophone, FaStop, FaTrash, FaPlay, FaTimes } from "react-icons/fa";
import "./styles.css"; // Import the CSS file

const API_BASE_URL = process.env.REACT_APP_API_URL;

console.log(API_BASE_URL);

export default function AudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcription, setTranscription] = useState("");
  const [outputData, setOutputData] = useState(null);
  const [showPopup, setShowPopup] = useState(false);
  const [audioURL, setAudioURL] = useState("");
  const [audioBlob, setAudioBlob] = useState(null);

  const mediaRecorderRef = useRef(null); // Reference to the MediaRecorder
  const streamRef = useRef(null); // Reference to the MediaStream

  // SpeechRecognition API (Web Speech API)
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;

  const startRecording = async () => {
    setIsRecording(true);
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream; // Store the stream reference
    const recorder = new MediaRecorder(stream);
    mediaRecorderRef.current = recorder; // Store the recorder reference
    const chunks = [];

    recorder.ondataavailable = (event) => {
      chunks.push(event.data);
    };

    recorder.onstop = async () => {
      const blob = new Blob(chunks, { type: "audio/webm" });
      setAudioBlob(blob);
      const url = URL.createObjectURL(blob);
      setAudioURL(url);
      setIsRecording(false);

      // Start the SpeechRecognition for transcription
      recognition.start();

      recognition.onresult = (event) => {
        let finalTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        setTranscription(finalTranscript); // Set transcription
      };

      recognition.onerror = (event) => {
        console.error("SpeechRecognition error", event.error);
        setIsRecording(false);
      };
    };

    recorder.start();
  };

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current;
    const stream = streamRef.current;

    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
      stream.getTracks().forEach((track) => track.stop()); // Stop the stream tracks correctly
      setIsRecording(false);

      // Stop the recognition process as well
      recognition.stop();
    }
  };

  const deleteAudio = () => {
    setAudioURL("");
    setAudioBlob(null);
  };

  // Handler for processing the transcription
  const handleProcessing = async () => {
    setIsProcessing(true);
    const response = await fetch(`${API_BASE_URL}/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcription }),
    });
    await response.json();
    setIsProcessing(false);
  };

  // Handler for optimizing: runs optimization scripts to add the processed prompt to the schedule
  const handleOptimzier = async () => {
    setIsOptimizing(true);

    try {
      const response = await fetch(`${API_BASE_URL}/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcription }), // Ensure JSON format
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! Status: ${response.status}, Message: ${errorText}`);
      }

      const data = await response.json();
      console.log("Response Data:", data);

      const rows = data.schedule.map((entry) => ({
        scan_id: entry.scan_id,
        scan_type: entry.scan_type,
        duration: entry.duration,
        priority: entry.priority,
        patient_id: entry.patient_id,
        check_in_date: entry.check_in_date || (entry.start_time ? entry.start_time.split(" ")[0] : "N/A"),
        check_in_time: entry.check_in_time || (entry.start_time ? entry.start_time.split(" ")[1] : "N/A"),
        unit: entry.machine || "Unknown",
      }));

      setOutputData(rows);
      setShowPopup(true);
    } catch (error) {
      console.error("Optimization failed:", error);
      alert(`Optimization failed: ${error.message}`);
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <div className="container">
      {/* Navigation Bar */}
      <header className="navbar">
        <h1>Welcome to the Medical Triaging Optimization System</h1>
      </header>

      {/* Main Content */}
      <main className="content">
        <p>Please press the buttons below to record and process your voice input.</p>

        {/* Action Buttons */}
        <div className="button-container">
          <button onClick={startRecording} disabled={isRecording} className="btn btn-record">
            <FaMicrophone /> {isRecording ? "Recording..." : "Start Recording"}
          </button>
          <button onClick={stopRecording} disabled={!isRecording} className="btn btn-rec-stop">
            <FaStop /> {isRecording ? "Stop Recording" : "Recording..."}
          </button>
          <button onClick={deleteAudio} disabled={isRecording} className="btn btn-abort">
            <FaTrash /> {isRecording ? "Recording..." : "Clear Recording"}
          </button>
          <button onClick={handleProcessing} disabled={isProcessing} className="btn btn-process">
            <FaPlay /> {isProcessing ? "Processing..." : "Run Processing"}
          </button>
          <button onClick={handleOptimzier} disabled={isOptimizing} className="btn btn-process">
            <FaPlay /> {isOptimizing ? "Optimizing..." : "Run Optimizer"}
          </button>
        </div>
      </main>

      {/* Popup Table for Output */}
      {showPopup && outputData && (
        <div className="popup">
          <div className="popup-content">
            <div className="popup-header">
              <h2>Schedule Preview</h2>
              <button onClick={() => setShowPopup(false)} className="close-btn">
                <FaTimes />
              </button>
            </div>
            <p>Displaying request information. Please verify all data is correct.</p>
            <table>
              <thead>
                <tr>
                  <th>Scan ID</th>
                  <th>Scan Type</th>
                  <th>Duration</th>
                  <th>Priority</th>
                  <th>Patient ID</th>
                  <th>Check In Date</th>
                  <th>Check In Time</th>
                  <th>Unit</th>
                </tr>
              </thead>
              <tbody>
                {outputData.map((row, index) => (
                  <tr key={index}>
                    <td>{row.scan_id}</td>
                    <td>{row.scan_type}</td>
                    <td>{row.duration}</td>
                    <td>{row.priority}</td>
                    <td>{row.patient_id}</td>
                    <td>{row.check_in_date}</td>
                    <td>{row.check_in_time}</td>
                    <td>{row.unit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="button-container">
              <button onClick={() => setShowPopup(false)} className="btn btn-close">
                Close
              </button>
              <button onClick={() => setShowPopup(false)} className="btn btn-commit">
                Commit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
