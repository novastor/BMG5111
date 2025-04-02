import React, { useState } from "react";
import { FaMicrophone, FaPlay, FaTimes } from "react-icons/fa";
import "./styles.css"; // Import the CSS file
const API_BASE_URL = process.env.REACT_APP_API_URL;
export default function AudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcription, setTranscription] = useState("");
  const [outputData, setOutputData] = useState(null);
  const [showPopup, setShowPopup] = useState(false);

  // Handler for recording audio
  const handleRecording = async () => {
    setIsRecording(true);
    const response = await fetch(`${API_BASE_URL}/record`, { method: "POST" });
    const data = await response.json();
    setTranscription(data.transcription);
    setIsRecording(false);
  };

  // Handler for processing the transcription (if needed)
  const handleProcessing = async () => {
    setIsProcessing(true);
    console.log("API_BASE_URL at render:", process.env.REACT_APP_API_URL);
    const response = await fetch(`${API_BASE_URL}/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcription }),
    });
    await response.json();
    
    setIsProcessing(false);
  };

  // Handler for optimizing: expects a list of dictionaries returned from backend
  const handleOptimzier = async () => {
    setIsOptimizing(true);
    console.log("API_BASE_URL:", API_BASE_URL)
    const response = await fetch(`${API_BASE_URL}/optimize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcription }),
    });
    
    // Get the JSON data (list of dictionaries) from the response
    const data = await response.json();
    console.log("response =" +response)

    // Process the list of dictionaries and structure them for display
    console.log("entry :" +data)
    const rows = data.schedule.map((entry) => ({
      scan_id: entry.scan_id,
      scan_type: entry.scan_type,
      duration: entry.duration,
      priority: entry.priority,
      patient_id: entry.patient_id,
      check_in_date: entry.start_time.split(" ")[0], // Extract date from start_time
      check_in_time: entry.start_time.split(" ")[1], // Extract time from start_time
      unit: entry.machine, // Assuming "machine" is the unit
    }));

    setOutputData(rows);
    setShowPopup(true);
    setIsOptimizing(false);
  };

  return (
    <div className="container">
      {/* Navigation Bar */}
      <header className="navbar">
        <h1>Welcome to the Medical Imaging Optimization Suite</h1>
      </header>
  
      {/* Main Content */}
      <main className="content">
        <p>Please press the buttons below to record and process your voice input.</p>
  
        {/* Action Buttons */}
        <div className="button-container">
          <button onClick={handleRecording} disabled={isRecording} className="btn btn-record">
            <FaMicrophone /> {isRecording ? "Recording..." : "Start Recording"}
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
              <button onClick={() => setShowPopup(false)} className="btn btn-close">Close</button>
              <button onClick={() => setShowPopup(false)} className="btn btn-commit">Commit</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
