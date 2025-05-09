// public/renderer.js

document.addEventListener("DOMContentLoaded", () => {
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

  const overlayCanvas = document.createElement("canvas");
  overlayCanvas.classList.add("face-overlay");

  overlayCanvas.style.position = "absolute";
  overlayCanvas.style.top = "0";
  overlayCanvas.style.left = "0";

  let currentDetection = null;

  let isLiveDetection = false;
  let detectionInterval = null;

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

  function startWebcam() {
    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        videoElement.srcObject = stream;
        infoElement.textContent =
          "Camera is active. Position your face in the frame.";

        // Add overlay canvas to container
        const cameraContainer = videoElement.parentElement;
        cameraContainer.appendChild(overlayCanvas);

        // Set initial size of overlay canvas
        overlayCanvas.width = cameraContainer.offsetWidth;
        overlayCanvas.height = cameraContainer.offsetHeight;

        // Update canvas size when video metadata is loaded
        videoElement.addEventListener("loadedmetadata", () => {
          // Start live detection after video is loaded
          toggleLiveDetection();
        });

        // Update canvas size whenever video is resized
        new ResizeObserver(() => {
          overlayCanvas.width = videoElement.clientWidth;
          overlayCanvas.height = videoElement.clientHeight;
        }).observe(videoElement);

        detectBtn.disabled = false;
      })
      .catch((err) => {
        infoElement.textContent = "Error accessing webcam: " + err.message;
        console.error("Webcam error:", err);
      });
  }

  function captureFrame() {
    const canvas = document.createElement("canvas");
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg");
  }

  function toggleLiveDetection() {
    isLiveDetection = !isLiveDetection;

    if (isLiveDetection) {
      if (detectBtn.textContent === "Detect Face") {
        detectBtn.textContent = "Stop Live Detection";
      }

      detectionInterval = setInterval(() => {
        if (videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
          runFaceDetection();
        }
      }, 200);
    } else {
      clearInterval(detectionInterval);
      detectBtn.textContent = "Start Live Detection";

      const ctx = overlayCanvas.getContext("2d");
      ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    }
  }

  function runFaceDetection() {
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
          console.error("Detection error:", data.error);
          return;
        }

        currentDetection = data;

        genderResult.textContent = data.gender;
        ageResult.textContent = data.age;

        if (genderConfidence && ageConfidence) {
          const genderConfidenceValue = data.gender_confidence || 0;
          const ageConfidenceValue = data.age_confidence || 0;
          genderConfidence.style.width = `${genderConfidenceValue}%`;
          ageConfidence.style.width = `${ageConfidenceValue}%`;
        }

        drawDetectionOverlay(data);

        saveBtn.disabled = false;
      })
      .catch((error) => {
        console.error("Detection error:", error);
      });
  }

  function drawDetectionOverlay(detection) {
    const ctx = overlayCanvas.getContext("2d");

    // Clear previous drawings
    ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

    if (detection.error || !detection.face_coords) {
      return;
    }

    // Get video dimensions
    const videoWidth = overlayCanvas.width;
    const videoHeight = overlayCanvas.height;

    // Get face coordinates as percentages and convert to pixels
    const faceX = detection.face_coords.x * videoWidth;
    const faceY = detection.face_coords.y * videoHeight;
    const faceWidth = detection.face_coords.width * videoWidth;
    const faceHeight = detection.face_coords.height * videoHeight;

    // Draw face box with animated effect
    const currentTime = new Date().getTime();
    const pulseAmount = Math.sin(currentTime / 300) * 3 + 2; // Pulsating effect

    ctx.strokeStyle =
      detection.gender === "Male"
        ? "rgba(0, 150, 255, 0.8)"
        : "rgba(255, 100, 200, 0.8)";
    ctx.lineWidth = pulseAmount;
    ctx.strokeRect(faceX, faceY, faceWidth, faceHeight);

    ctx.shadowColor =
      detection.gender === "Male"
        ? "rgba(0, 150, 255, 0.7)"
        : "rgba(255, 100, 200, 0.7)";
    ctx.shadowBlur = 15;

    const padding = 10;
    const boxWidth = 130;
    const boxHeight = 60;

    let boxX = faceX + faceWidth + padding;
    if (boxX + boxWidth > videoWidth) {
      boxX = faceX - boxWidth - padding;
    }

    const boxY = faceY + faceHeight / 2 - boxHeight / 2;

    ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
    ctx.fillRect(boxX, boxY, boxWidth, boxHeight);

    ctx.shadowBlur = 0;
    ctx.font = "16px Arial";
    ctx.fillStyle = "white";
    ctx.textAlign = "left";
    ctx.fillText(`Gender: ${detection.gender}`, boxX + 10, boxY + 25);
    ctx.fillText(`Age: ${detection.age}`, boxX + 10, boxY + 45);
  }

  detectBtn.addEventListener("click", toggleLiveDetection);

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

        const now = new Date();
        timestampResult.textContent = now.toLocaleString();
      })
      .catch((error) => {
        infoElement.textContent = "Error saving to database";
        console.error("Database save error:", error);
      });
  });

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

          // Reset confidence bars if they exist
          if (genderConfidence && ageConfidence) {
            genderConfidence.style.width = "0%";
            ageConfidence.style.width = "0%";
          }

          // Update current detection
          currentDetection = {
            gender: data.gender,
            age: data.age,
          };

          // Enable save button
          saveBtn.disabled = false;
        }
      })
      .catch((error) => {
        infoElement.textContent = "Error fetching from database";
        console.error("Database fetch error:", error);
      });
  });
});
