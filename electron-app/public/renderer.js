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

  container.appendChild(num1Input);
  container.appendChild(num2Input);
  container.appendChild(calculateButton);
  container.appendChild(resultElement);

  document.body.appendChild(container);

  // Add event listener to the button
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
        resultElement.textContent = `Result: ${data.result}`;
      })
      .catch((error) => {
        resultElement.textContent = "Error calculating result";
        console.error("Calculation error:", error);
      });
  });
});
