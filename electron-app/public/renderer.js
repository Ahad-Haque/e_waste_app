// public/renderer.js

document.addEventListener("DOMContentLoaded", () => {
  const infoElement = document.getElementById("info");

  // Test connection to Python backend
  fetch("http://127.0.0.1:5000/test")
    .then((response) => response.json())
    .then((data) => {
      infoElement.textContent = data.message;
      console.log("Backend connection successful:", data);
    })
    .catch((error) => {
      infoElement.textContent = "Error connecting to Python backend";
      console.error("Backend connection error:", error);
    });

  // Create UI elements for multiplication
  const container = document.createElement("div");

  const num1Input = document.createElement("input");
  num1Input.type = "number";
  num1Input.placeholder = "Enter first number";

  const num2Input = document.createElement("input");
  num2Input.type = "number";
  num2Input.placeholder = "Enter second number";

  const calculateButton = document.createElement("button");
  calculateButton.textContent = "Multiply";

  const resultElement = document.createElement("div");
  resultElement.id = "result";

  // Create Save and Fetch buttons
  const saveButton = document.createElement("button");
  saveButton.textContent = "Save Result";
  saveButton.style.marginRight = "10px";

  const fetchButton = document.createElement("button");
  fetchButton.textContent = "Fetch Previous";

  const dbStatusElement = document.createElement("div");
  dbStatusElement.id = "db-status";
  dbStatusElement.style.marginTop = "10px";
  dbStatusElement.style.color = "#666";

  // Add all elements to container
  container.appendChild(num1Input);
  container.appendChild(num2Input);
  container.appendChild(calculateButton);
  container.appendChild(resultElement);

  // Add DB operation elements
  const dbContainer = document.createElement("div");
  dbContainer.style.marginTop = "20px";
  dbContainer.appendChild(saveButton);
  dbContainer.appendChild(fetchButton);
  dbContainer.appendChild(dbStatusElement);

  container.appendChild(dbContainer);
  document.body.appendChild(container);

  // Keep track of the current result
  let currentResult = null;

  // Add event listener to the calculate button
  calculateButton.addEventListener("click", () => {
    const num1 = parseInt(num1Input.value) || 0;
    const num2 = parseInt(num2Input.value) || 0;

    fetch("http://127.0.0.1:5000/multiply", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ num1, num2 }),
    })
      .then((response) => response.json())
      .then((data) => {
        currentResult = data.result;
        resultElement.textContent = `Result: ${currentResult}`;
      })
      .catch((error) => {
        resultElement.textContent = "Error calculating result";
        console.error("Calculation error:", error);
      });
  });

  // Add event listener to the save button
  saveButton.addEventListener("click", () => {
    if (currentResult === null) {
      dbStatusElement.textContent = "No result to save. Calculate first.";
      return;
    }

    fetch("http://127.0.0.1:5000/save-result", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ result: currentResult }),
    })
      .then((response) => response.json())
      .then((data) => {
        dbStatusElement.textContent = `Database: ${data.message}`;
      })
      .catch((error) => {
        dbStatusElement.textContent = "Error saving to database";
        console.error("Database save error:", error);
      });
  });

  // Add event listener to the fetch button
  fetchButton.addEventListener("click", () => {
    fetch("http://127.0.0.1:5000/fetch-result")
      .then((response) => response.json())
      .then((data) => {
        if (data.result === "NA") {
          dbStatusElement.textContent = "Database: No previous result found";
        } else {
          dbStatusElement.textContent = `Previous result: ${data.result}`;
          // Optionally update the current result
          currentResult = data.result;
        }
      })
      .catch((error) => {
        dbStatusElement.textContent = "Error fetching from database";
        console.error("Database fetch error:", error);
      });
  });
});
