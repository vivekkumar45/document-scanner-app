import os
import sqlite3
import hashlib
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# File Upload Configuration
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize the database and create tables if they don't exist
def init_db():
    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        credits INTEGER DEFAULT 20,
        last_reset DATE DEFAULT NULL
    )''')

    # Create credit requests table
    cursor.execute('''CREATE TABLE IF NOT EXISTS credit_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        status TEXT CHECK(status IN ('pending', 'approved', 'denied')) DEFAULT 'pending'
    )''')

    # Create documents table
    cursor.execute('''CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        filename TEXT NOT NULL,
        content TEXT NOT NULL
    )''')

    conn.commit()
    conn.close()

# Call function to ensure the database is set up
init_db()

# Function to reset credits at midnight
def reset_daily_credits(username):
    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT last_reset FROM users WHERE username = ?", (username,))
    last_reset = cursor.fetchone()

    today = datetime.now().date()

    if last_reset is None or last_reset[0] != str(today):
        cursor.execute("UPDATE users SET credits = 20, last_reset = ? WHERE username = ?", (today, username))
        conn.commit()

    conn.close()

# Home Route
@app.route("/")
def home():
    return "Document Scanner API is running!"

# User Registration
@app.route("/auth/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = hash_password(data.get("password"))

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, password, credits, last_reset) VALUES (?, ?, 20, NULL)", (username, password))
        conn.commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"message": "Username already exists!"}), 400
    finally:
        conn.close()

# User Login
@app.route("/auth/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = hash_password(data.get("password"))

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    # Reset credits if needed
    reset_daily_credits(username)

    cursor.execute("SELECT credits FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful!", "credits": user[0]}), 200
    else:
        return jsonify({"message": "Invalid username or password!"}), 401

# Document Scan (Deducts 1 Credit)
@app.route("/scan", methods=["POST"])
def scan_document():
    data = request.json
    username = data.get("username")

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    # Reset credits if needed
    reset_daily_credits(username)

    cursor.execute("SELECT credits FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user and user[0] > 0:
        new_credits = user[0] - 1
        cursor.execute("UPDATE users SET credits = ? WHERE username = ?", (new_credits, username))
        conn.commit()
        conn.close()
        return jsonify({"message": "Scan successful!", "remaining_credits": new_credits}), 200
    else:
        conn.close()
        return jsonify({"message": "Not enough credits! Request more credits."}), 403

# Request More Credits
@app.route("/credits/request", methods=["POST"])
def request_credits():
    data = request.json
    username = data.get("username")

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    # Checking  if the user already has a pending request
    cursor.execute("SELECT * FROM credit_requests WHERE username = ? AND status = 'pending'", (username,))
    existing_request = cursor.fetchone()

    if existing_request:
        conn.close()
        return jsonify({"message": "You already have a pending credit request!"}), 400

    cursor.execute("INSERT INTO credit_requests (username, status) VALUES (?, 'pending')", (username,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Credit request submitted!"}), 201

# Admin Approve or Deny Credit Requests
@app.route("/admin/credits/approve", methods=["POST"])
def approve_credits():
    data = request.json
    username = data.get("username")
    action = data.get("action")  # "approve" or "deny"

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM credit_requests WHERE username = ? AND status = 'pending'", (username,))
    request_exists = cursor.fetchone()

    if not request_exists:
        conn.close()
        return jsonify({"message": "No pending request for this user!"}), 400

    if action == "approve":
        cursor.execute("UPDATE users SET credits = credits + 10 WHERE username = ?", (username,))
        cursor.execute("UPDATE credit_requests SET status = 'approved' WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Credits approved! 10 credits added."}), 200
    elif action == "deny":
        cursor.execute("UPDATE credit_requests SET status = 'denied' WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Credit request denied!"}), 200
    else:
        conn.close()
        return jsonify({"message": "Invalid action. Use 'approve' or 'deny'."}), 400

# File Upload Route
@app.route("/upload", methods=["POST"])
def upload_file():
    username = request.form.get("username")
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Saving file content to database
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO documents (username, filename, content) VALUES (?, ?, ?)", (username, filename, content))
    conn.commit()
    conn.close()

    return jsonify({"message": "File uploaded successfully!"}), 200

# Function to match documents
@app.route("/match", methods=["POST"])
def match_documents():
    data = request.json
    username = data.get("username")
    query_text = data.get("query_text")

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT filename, content FROM documents WHERE username = ?", (username,))
    documents = cursor.fetchall()

    matched_files = [filename for filename, content in documents if query_text.lower() in content.lower()]
    conn.close()

    return jsonify({"matched_files": matched_files}), 200


if __name__ == "__main__":
    app.run(debug=True)
