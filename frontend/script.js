const BASE_URL = "http://127.0.0.1:5000";

// Function to register user
function registerUser() {
    const username = document.getElementById("reg-username").value;
    const password = document.getElementById("reg-password").value;

    fetch(`${BASE_URL}/auth/register`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("message").textContent = data.message;
    })
    .catch(error => console.error("Error:", error));
}

// Function to log in user
function loginUser() {
    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;

    fetch(`${BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            document.getElementById("message").textContent = `Welcome! You have ${data.credits} credits.`;
        } else {
            document.getElementById("message").textContent = "Invalid username or password!";
        }
    })
    .catch(error => console.error("Error:", error));
}
