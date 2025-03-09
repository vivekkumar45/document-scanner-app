import sqlite3
import os
import hashlib

# Get the absolute path to the database directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Backend directory
DB_DIR = os.path.join(BASE_DIR, "../database")  # Adjusted path
DB_PATH = os.path.join(DB_DIR, "users.db")

# Ensure database directory exists
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Connected to SQLite database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Created users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Insert sample user securely (Optional)
hashed_password = hash_password("securepassword")  # Hash password before storing
cursor.execute("INSERT OR IGNORE INTO users (username, email, password) VALUES (?, ?, ?)", 
               ("testuser", "test@example.com", hashed_password))

# Save changes and close connection
conn.commit()
conn.close()

print(f"✅ Database initialized successfully at {DB_PATH}")
