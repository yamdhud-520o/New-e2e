# database.py
import sqlite3
import hashlib
import os
import tempfile

# Render.com ke liye - temporary folder mein database banegi
DB_PATH = os.path.join(tempfile.gettempdir(), 'users.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # User configs table
    c.execute('''CREATE TABLE IF NOT EXISTS user_configs (
        user_id INTEGER PRIMARY KEY,
        chat_id TEXT,
        name_prefix TEXT,
        delay INTEGER DEFAULT 5,
        cookies TEXT,
        messages TEXT,
        automation_running INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # Admin E2EE threads table
    c.execute('''CREATE TABLE IF NOT EXISTS admin_e2ee_threads (
        user_id INTEGER PRIMARY KEY,
        thread_id TEXT,
        cookies TEXT,
        chat_type TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

def create_user(username, password):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        user_id = c.lastrowid
        c.execute("INSERT INTO user_configs (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists!"

def verify_user(username, password):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    hashed = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed))
    result = c.fetchone()
    conn.close()
    
    return result[0] if result else None

def get_user_config(user_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT chat_id, name_prefix, delay, cookies, messages FROM user_configs WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'chat_id': result[0] or '',
            'name_prefix': result[1] or '',
            'delay': result[2] or 5,
            'cookies': result[3] or '',
            'messages': result[4] or ''
        }
    return None

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""UPDATE user_configs 
                 SET chat_id = ?, name_prefix = ?, delay = ?, cookies = ?, messages = ?
                 WHERE user_id = ?""",
              (chat_id, name_prefix, delay, cookies, messages, user_id))
    conn.commit()
    conn.close()

def get_automation_running(user_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT automation_running FROM user_configs WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    return bool(result[0]) if result else False

def set_automation_running(user_id, status):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("UPDATE user_configs SET automation_running = ? WHERE user_id = ?", (1 if status else 0, user_id))
    conn.commit()
    conn.close()

def get_username(user_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    return result[0] if result else None

def get_admin_e2ee_thread_id(user_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT thread_id FROM admin_e2ee_threads WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    return result[0] if result else None

def set_admin_e2ee_thread_id(user_id, thread_id, cookies, chat_type):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""INSERT OR REPLACE INTO admin_e2ee_threads (user_id, thread_id, cookies, chat_type)
                 VALUES (?, ?, ?, ?)""", (user_id, thread_id, cookies, chat_type))
    conn.commit()
    conn.close()
