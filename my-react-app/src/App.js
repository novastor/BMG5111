import React, { useState, useRef } from "react";
import { FaMicrophone, FaStop, FaTrash, FaPlay, FaTimes } from "react-icons/fa";
import { FFmpeg } from "@ffmpeg/ffmpeg";  // Correct import
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

  const ffmpeg = FFmpeg.createFFmpeg({ log: true });  // Correct way to create FFmpeg instance
    // Start recording using MediaRecorder
    const startRecording = async () => {
      setErrorMessage("");
      setTranscription(""); // clear any previous transcript
      try {
        setIsRecording(true);
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;
        const chunks = [];
  
        recorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            chunks.push(event.data);
          }
        };
  
        recorder.onstop = async () => {
          setIsRecording(false);
          const blob = new Blob(chunks, { type: "audio/webm" });
          console.log("Recorded audio blob:", blob);
  
          // Convert the blob to wav format using ffmpeg
          setIsConverting(true);
          await ffmpeg.load();
          const fileName = "recording.webm";
          const fileData = new Uint8Array(await blob.arrayBuffer());
  
          // Write the recorded file to FFmpeg's virtual file system
          ffmpeg.FS("writeFile", fileName, fileData);
  
          // Convert webm to wav using FFmpeg
          await ffmpeg.run("-i", fileName, "output.wav");
  
          // Read the converted wav file
          const outputWav = ffmpeg.FS("readFile", "output.wav");
          const wavBlob = new Blob([outputWav.buffer], { type: "audio/wav" });
  
          // Now you can upload the converted wav file to the server
          const formData = new FormData();
          formData.append("file", wavBlob, "recording.wav");
  
          try {
            const response = await fetch(`${API_BASE_URL}/record`, {
              method: "POST",
              body: formData,
            });
            if (!response.ok) {
              throw new Error(`HTTP error: status ${response.status}`);
            }
            const result = await response.json();
            console.log("Transcription received:", result.transcription);
            // Store the actual transcript returned by the backend
            setTranscription(result.transcription);
          } catch (error) {
            console.error("Error uploading audio:", error);
            setErrorMessage("Error uploading audio: " + error.message);
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
  
    // Stop recording and release media resources
    const stopRecording = () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
        }
        setIsRecording(false);
      }
    };
  
    // Delete the displayed transcription and any output
    const deleteAudio = () => {
      setTranscription("");
      setOutputData(null);
      setErrorMessage("");
    };
  
    // Send the transcription to the backend to optimize the workflow
    const handleOptimize = async () => {
      if (!transcription) {
        setErrorMessage("No transcription available for optimization.");
        return;
      }
      setErrorMessage("");
      setIsOptimizing(true);
      try {
        const response = await fetch(`${API_BASE_URL}/optimize`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ transcription }),
        });
        if (!response.ok) {
          throw new Error(`HTTP error: status ${response.status}`);
        }
        const data = await response.json();
        console.log("Optimization response:", data.schedule);
        setOutputData(data.schedule);
        setShowPopup(true);
      } catch (error) {
        console.error("Optimization error:", error);
        setErrorMessage("Optimization failed: " + error.message);
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
            <button onClick={startRecording} disabled={isRecording || isConverting} className="btn btn-record">
              <FaMicrophone /> {isRecording ? "Recording..." : "Start Recording"}
            </button>
            <button onClick={stopRecording} disabled={!isRecording} className="btn btn-rec-stop">
              <FaStop /> Stop Recording
            </button>
            <button onClick={deleteAudio} disabled={!transcription} className="btn btn-abort">
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
  