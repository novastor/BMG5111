import React, { useState, useRef, useEffect } from "react";
import { FaMicrophone, FaStop, FaTrash, FaPlay, FaTimes } from "react-icons/fa";
import "./styles.css";

const API_BASE_URL = process.env.REACT_APP_API_URL;

export default function AudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [transcription, setTranscription] = useState("");
  const [outputData, setOutputData] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [showPopup, setShowPopup] = useState(false);
  const [isConverting, setIsConverting] = useState(false);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    navigator.mediaDevices
      .enumerateDevices()
      .then((devices) => {
        devices.forEach((device) => {
          console.log(device.kind, device.label);
        });
      })
      .catch((err) => {
        console.error("Error enumerating devices:", err);
      });
  }, []);

  const startRecording = async () => {
    setErrorMessage("");
    setTranscription(""); // Clear previous transcription
    try {
      setIsRecording(true);
      // Request permission for the audio stream
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      // Check for Firefox-compatible MIME type (preferred: audio/ogg; codecs=opus)
      const mimeType = MediaRecorder.isTypeSupported("audio/ogg; codecs=opus")
        ? "audio/ogg; codecs=opus"
        : "audio/webm"; // fallback to WebM
      
      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      // Collect audio data chunks
      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // When recording stops, process the audio data
      recorder.onstop = async () => {
        setIsRecording(false);
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        console.log("Recorded audio blob:", blob);
      
        setIsConverting(true);
        try {
          // Prepare form data to send the audio blob
          const formData = new FormData();
          formData.append("file", blob, mimeType.includes("ogg") ? "recording.ogg" : "recording.webm");
      
          // Send blob to the /record endpoint for transcription
          const response = await fetch(`${API_BASE_URL}/record`, {
            method: "POST",
            body: formData,
          });
          if (!response.ok) {
            throw new Error(`HTTP error: status ${response.status}`);
          }
          const result = await response.json();
          console.log("Transcription received:", result.transcription);
          setTranscription(result.transcription);
        } catch (uploadError) {
          console.error("Error uploading audio:", uploadError);
          setErrorMessage("Error uploading audio: " + uploadError.message);
        } finally {
          setIsConverting(false);
        }
      };

      recorder.start();
    } catch (error) {
      console.error("Error accessing microphone:", error);
      setErrorMessage("Error accessing microphone: " + error.message);
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      setIsRecording(false);
    }
  };

  const deleteAudio = () => {
    setTranscription(""); // Clear the transcription
    setOutputData(null);   // Clear any previous output data
    setErrorMessage("");   // Clear any error messages
  };

  const handleOptimize = async () => {
    if (!transcription) {
      setErrorMessage("No transcription available for optimization.");
      return;
    }
    setErrorMessage(""); // Clear any previous error
    setIsOptimizing(true); // Start loading indicator
    try {
      const response = await fetch(`${API_BASE_URL}/optimize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ transcription }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error: status ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Optimization response:", data.schedule);
      setOutputData(data.schedule); // Set the output data for the optimized schedule
      setShowPopup(true); // Show the popup with the optimized schedule
    } catch (optimizeError) {
      console.error("Optimization error:", optimizeError);
      setErrorMessage("Optimization failed: " + optimizeError.message);
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <div className="container">
      <header className="navbar">
        <h1>Medical Triaging Optimization System</h1>
      </header>

      <main className="content">
        <p>
          Please record your voice input to generate a transcript. Once the transcript appears, you can optimize it.
        </p>
        {errorMessage && <p className="error">{errorMessage}</p>}
        <div className="button-container">
          <button
            onClick={startRecording}
            disabled={isRecording || isConverting}
            className="btn btn-record"
          >
            <FaMicrophone /> {isRecording ? "Recording..." : "Start Recording"}
          </button>
          <button
            onClick={stopRecording}
            disabled={!isRecording}
            className="btn btn-rec-stop"
          >
            <FaStop /> Stop Recording
          </button>
          <button
            onClick={deleteAudio}
            disabled={!transcription}
            className="btn btn-abort"
          >
            <FaTrash /> Clear Transcript
          </button>
          <button
            onClick={handleOptimize}
            disabled={isOptimizing || !transcription}
            className="btn btn-process"
          >
            <FaPlay /> {isOptimizing ? "Optimizing..." : "Optimize"}
          </button>
        </div>
        {transcription && (
          <div className="transcript-display">
            <h3>Transcription:</h3>
            <p>{transcription}</p>
          </div>
        )}
      </main>

      {/* Popup for Optimized Schedule */}
      {showPopup && outputData && (
        <div className="popup">
          <div className="popup-content">
            <div className="popup-header">
              <h2>Schedule Preview</h2>
              <button onClick={() => setShowPopup(false)} className="close-btn">
                <FaTimes />
              </button>
            </div>
            <p>Below is the optimized schedule. Please verify the details.</p>
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
                    <td>{row.machine}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="button-container">
              <button onClick={() => setShowPopup(false)} className="btn btn-close">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
