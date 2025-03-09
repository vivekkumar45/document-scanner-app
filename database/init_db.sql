-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    credits INTEGER DEFAULT 20,
    last_reset DATE DEFAULT NULL
);

-- Create the credit requests table
CREATE TABLE IF NOT EXISTS credit_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    status TEXT CHECK(status IN ('pending', 'approved', 'denied')) DEFAULT 'pending'
);

-- Create the documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    filename TEXT NOT NULL,
    content TEXT NOT NULL
);

-- Insert a test user (Optional)
INSERT OR IGNORE INTO users (username, password, credits, last_reset) 
VALUES ('testuser', 'testpassword', 20, NULL);
