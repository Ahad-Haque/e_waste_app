// public/renderer.js

document.addEventListener("DOMContentLoaded", () => {
  // DOM elements
  const infoElement = document.getElementById("info");
  const videoElement = document.getElementById("camera-view");
  const detectBtn = document.getElementById("detect-btn");
  const saveBtn = document.getElementById("save-btn");
  const fetchBtn = document.getElementById("fetch-btn");
  const genderResult = document.getElementById("gender-result");
  const ageResult = document.getElementById("age-result");
  const timestampResult = document.getElementById("timestamp-result");
  const genderConfidence = document.getElementById("gender-confidence");
  const ageConfidence = document.getElementById("age-confidence");

  // Current detection results
  let currentDetection = null;

  // Test connection to Python backend
  fetch("http://127.0.0.1:5000/test")
    .then((response) => response.json())
    .then((data) => {
      infoElement.textContent = data.message;
      console.log("Backend connection successful:", data);
      startWebcam();
    })
    .catch((error) => {
      infoElement.textContent =
        "Error connecting to Python backend. Make sure it's running!";
      console.error("Backend connection error:", error);
    });

  // Initialize webcam
  function startWebcam() {
    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        videoElement.srcObject = stream;
        infoElement.textContent =
          "Camera is active. Position your face in the square and click 'Detect Face'";
        detectBtn.disabled = false;
      })
      .catch((err) => {
        infoElement.textContent = "Error accessing webcam: " + err.message;
        console.error("Webcam error:", err);
      });
  }

  // Capture current frame from webcam
  function captureFrame() {
    const canvas = document.createElement("canvas");
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg");
  }

  // Detect face, age, and gender
  detectBtn.addEventListener("click", () => {
    if (!videoElement.srcObject) {
      infoElement.textContent = "Camera not ready yet. Please wait...";
      return;
    }

    infoElement.textContent = "Processing...";
    const imageData = captureFrame();

    fetch("http://127.0.0.1:5000/detect-face", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ image: imageData }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          infoElement.textContent = "Detection error: " + data.error;
          return;
        }

        currentDetection = data;
        genderResult.textContent = data.gender;
        ageResult.textContent = data.age;

        // Update confidence bars
        const genderConfidenceValue = data.gender_confidence || 0;
        const ageConfidenceValue = data.age_confidence || 0;
        genderConfidence.style.width = `${genderConfidenceValue}%`;
        ageConfidence.style.width = `${ageConfidenceValue}%`;

        timestampResult.textContent = "(not saved yet)";
        infoElement.textContent =
          "Face detected! Click 'Save Data' to store this information.";
        saveBtn.disabled = false;
      })
      .catch((error) => {
        infoElement.textContent = "Error processing image";
        console.error("Detection error:", error);
      });
  });

  // Save detected data
  saveBtn.addEventListener("click", () => {
    if (!currentDetection) {
      infoElement.textContent = "No face data to save. Detect a face first.";
      return;
    }

    fetch("http://127.0.0.1:5000/save-face-data", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        gender: currentDetection.gender,
        age: currentDetection.age,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        infoElement.textContent = `Data saved successfully!`;

        // Update timestamp with current time (approximate)
        const now = new Date();
        timestampResult.textContent = now.toLocaleString();
      })
      .catch((error) => {
        infoElement.textContent = "Error saving to database";
        console.error("Database save error:", error);
      });
  });

  // Fetch latest saved data
  fetchBtn.addEventListener("click", () => {
    fetch("http://127.0.0.1:5000/fetch-latest")
      .then((response) => response.json())
      .then((data) => {
        if (data.message === "No data found") {
          infoElement.textContent = "No previous data found in database";
        } else {
          infoElement.textContent = "Latest data retrieved!";
          genderResult.textContent = data.gender;
          ageResult.textContent = data.age;
          timestampResult.textContent = data.timestamp;

          // Reset confidence bars as we don't have confidence for fetched data
          genderConfidence.style.width = "0%";
          ageConfidence.style.width = "0%";

          // Update current detection
          currentDetection = {
            gender: data.gender,
            age: data.age,
          };

          // Enable save button in case user wants to save again
          saveBtn.disabled = false;
        }
      })
      .catch((error) => {
        infoElement.textContent = "Error fetching from database";
        console.error("Database fetch error:", error);
      });
  });
});
