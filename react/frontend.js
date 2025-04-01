import { useState } from "react";

function App() {
    const [transcription, setTranscription] = useState("");

    const startRecording = async () => {
        try {
            const response = await fetch("http://127.0.0.1:5000/record", {
                method: "POST"
            });
            const data = await response.json();
            setTranscription(data.transcription);
        } catch (error) {
            console.error("Error:", error);
        }
    };

    return (
        <div style={{ textAlign: "center", marginTop: "50px" }}>
            <h1>Speech to Text</h1>
            <button onClick={startRecording}>Start Recording</button>
            <p><b>Transcription:</b> {transcription}</p>
        </div>
    );
}

export default App;
