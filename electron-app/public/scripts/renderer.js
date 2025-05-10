// electron-app\public\scripts\renderer.js
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM loaded, initializing...");

  const videoElement = document.getElementById("camera-view");
  const genderResult = document.getElementById("gender-result");
  const ageResult = document.getElementById("age-result");
  const vipAvatar = document.getElementById("vip-avatar");
  const vipName = document.getElementById("vip-name");
  const vipStatus = document.getElementById("vip-status");

  let isDetecting = false;
  let detectionInterval = null;
  let currentVIPState = null;
  let stream = null;

  // VIP state management queue
  let vipQueue = new Map();

  // Initialize camera immediately
  initializeCamera();

  function initializeCamera() {
    console.log("Attempting to initialize camera...");
    vipStatus.textContent = "Requesting camera access...";

    // Check if browser supports getUserMedia
    if (!navigator.mediaDevices?.getUserMedia) {
      console.error("getUserMedia not supported");
      vipStatus.textContent = "Camera not supported!";
      return;
    }

    // Request camera access with different constraints
    const constraints = {
      video: {
        width: { ideal: 1280, min: 640 },
        height: { ideal: 720, min: 480 },
        frameRate: { ideal: 30, min: 15 },
      },
      audio: false,
    };

    navigator.mediaDevices
      .getUserMedia(constraints)
      .then((mediaStream) => {
        console.log("Camera access granted!");
        stream = mediaStream;
        videoElement.srcObject = stream;
        vipStatus.textContent = "Camera active";

        // Handle video events
        videoElement.onloadedmetadata = () => {
          console.log("Video metadata loaded");
          videoElement.play();
        };

        videoElement.onplaying = () => {
          console.log("Video is playing");
          vipStatus.textContent = "Camera running";
          startFaceDetection();
        };

        videoElement.onerror = (e) => {
          console.error("Video error:", e);
          vipStatus.textContent = "Video error!";
        };
      })
      .catch((err) => {
        console.error("Initial camera access failed:", err);
        console.log("Error name:", err.name);
        console.log("Error message:", err.message);

        // Try with minimal constraints
        navigator.mediaDevices
          .getUserMedia({ video: true })
          .then((fallbackStream) => {
            console.log("Fallback camera access successful!");
            stream = fallbackStream;
            videoElement.srcObject = stream;
            vipStatus.textContent = "Camera active (basic)";

            videoElement.onplaying = () => {
              startFaceDetection();
            };
          })
          .catch((fallbackErr) => {
            console.error("Fallback camera access failed:", fallbackErr);
            vipStatus.textContent = `Camera denied: ${fallbackErr.message}`;

            // Last resort: try enumerating devices
            navigator.mediaDevices
              .enumerateDevices()
              .then((devices) => {
                console.log("Available devices:", devices);
                const videoDevices = devices.filter(
                  (device) => device.kind === "videoinput"
                );
                console.log("Video devices:", videoDevices);

                if (videoDevices.length === 0) {
                  vipStatus.textContent = "No camera found!";
                } else {
                  vipStatus.textContent = `${videoDevices.length} camera(s) found, but access denied`;
                }
              })
              .catch((enumErr) => {
                console.error("Device enumeration failed:", enumErr);
                vipStatus.textContent = "Camera system error!";
              });
          });
      });
  }

  function startFaceDetection() {
    if (isDetecting) return;

    isDetecting = true;
    detectionInterval = setInterval(() => {
      if (videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
        detectFace();
      }
    }, 200); // Check every 200ms for better responsiveness
  }

  function stopFaceDetection() {
    isDetecting = false;
    if (detectionInterval) {
      clearInterval(detectionInterval);
      detectionInterval = null;
    }
  }

  function captureFrame() {
    const canvas = document.createElement("canvas");
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.8);
  }

  function detectFace() {
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
        updateUI(data);
      })
      .catch((error) => {
        console.error("Detection error:", error);
        updateUI({ error: "Detection failed" });
      });
  }

  function updateUI(data) {
    // Always check for new VIPs or changes
    const detectedVIP = checkIfVIP(data);

    if (data.error) {
      // No face detected
      genderResult.textContent = "--";
      ageResult.textContent = "--";
      vipStatus.textContent = "Looking for face...";

      // If no VIP is currently active, show default
      if (!currentVIPState) {
        vipName.textContent = "No VIP";
        vipAvatar.src = "./assets/avatars/default.png";
      }
      return;
    }

    // Update detection info
    genderResult.textContent = data.gender || "--";
    ageResult.textContent = data.age || "--";

    // Handle VIP detection and state management
    if (detectedVIP) {
      handleVIPDetection(detectedVIP, data);
    } else {
      // Non-VIP detected
      currentVIPState = null;
      vipName.textContent = "Guest";
      vipStatus.textContent = "Not registered";
      vipAvatar.src = "./assets/avatars/default.png";

      // Start fresh flow for guest
      if (window.flowManager) {
        window.flowManager.showState("ewaste-selection");
      }
    }
  }

  function handleVIPDetection(vipId, detectionData) {
    // Check if this is a different VIP than currently active
    if (currentVIPState !== vipId) {
      // Save current VIP's state if exists
      if (currentVIPState && window.flowManager) {
        vipQueue.set(currentVIPState, {
          flowState: window.flowManager.currentFlow,
          selectedBox: window.flowManager.selectedBox,
          selectedRating: window.flowManager.selectedRating,
          timestamp: Date.now(),
        });
        console.log(`Saved state for VIP ${currentVIPState}`);
      }

      // Switch to new VIP
      currentVIPState = vipId;
      vipName.textContent = `VIP ${vipId}`;
      vipStatus.textContent = "Active";
      vipAvatar.src = `./assets/avatars/vip${vipId}.png`;

      // Restore VIP's state if exists
      if (vipQueue.has(vipId)) {
        const savedState = vipQueue.get(vipId);
        console.log(`Restoring state for VIP ${vipId}:`, savedState);

        if (window.flowManager) {
          // Restore flow state
          window.flowManager.currentFlow = savedState.flowState;
          window.flowManager.selectedBox = savedState.selectedBox;
          window.flowManager.selectedRating = savedState.selectedRating;
          window.flowManager.showState(savedState.flowState);

          // If VIP was at box instruction, they're returning
          if (savedState.flowState === "box-instruction") {
            // Give them a moment to return, then show thank you
            setTimeout(() => {
              window.flowManager.showThankYou();
            }, 1000);
          }
        }
      } else {
        // New VIP - start fresh flow
        console.log(`New VIP ${vipId} detected`);
        if (window.flowManager) {
          window.flowManager.showState("ewaste-selection");
        }
      }
    } else {
      // Same VIP - just update status
      vipStatus.textContent = "Active";
    }
  }

  function checkIfVIP(data) {
    // Placeholder VIP detection logic
    // In a real app, this would use proper face recognition
    if (!data || data.error) return false;

    const age = parseInt(data.age);
    const gender = data.gender;

    // Mock VIP detection based on age and gender
    // Replace this with actual face recognition logic
    if (age >= 20 && age <= 25 && gender === "Male") return 1;
    if (age >= 26 && age <= 30 && gender === "Female") return 2;
    if (age >= 31 && age <= 35 && gender === "Male") return 3;
    if (age >= 36 && age <= 40 && gender === "Female") return 4;
    if (age >= 41 && age <= 45 && gender === "Male") return 5;
    if (age >= 46 && age <= 50 && gender === "Female") return 6;
    if (age >= 51 && gender === "Male") return 7;

    return false; // Not a VIP
  }

  // Store reference for flow manager integration
  window.cameraManager = {
    takePhoto: function () {
      // Capture photo for 5-star rating flow
      const photoData = captureFrame();

      // Save to database (implement later)
      fetch("http://127.0.0.1:5000/save-photo", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          photo: photoData,
          vipId: currentVIPState,
          timestamp: new Date().toISOString(),
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Photo saved:", data);
        })
        .catch((error) => {
          console.error("Error saving photo:", error);
        });

      return photoData;
    },

    getCurrentVIP: function () {
      return currentVIPState;
    },

    clearVIPState: function (vipId) {
      if (vipQueue.has(vipId)) {
        vipQueue.delete(vipId);
      }
      if (currentVIPState === vipId) {
        currentVIPState = null;
      }
    },
  };

  // Clean up when window closes
  window.addEventListener("beforeunload", () => {
    stopFaceDetection();
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
  });

  // Error handler for avatar images
  vipAvatar.onerror = function () {
    this.src = "./assets/avatars/default.png";
  };

  // Log VIP queue periodically (for debugging)
  setInterval(() => {
    if (vipQueue.size > 0) {
      console.log("Current VIP queue:", Object.fromEntries(vipQueue));
    }
  }, 30000); // Every 30 seconds

  // Add a manual retry button
  const retryButton = document.createElement("button");
  retryButton.textContent = "Retry Camera";
  retryButton.style.position = "absolute";
  retryButton.style.top = "10px";
  retryButton.style.right = "10px";
  retryButton.style.zIndex = "1000";
  retryButton.onclick = () => {
    console.log("Manual camera retry...");
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
    initializeCamera();
  };
  document.body.appendChild(retryButton);
});
