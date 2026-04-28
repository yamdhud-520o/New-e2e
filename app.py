from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import time
import threading
import hashlib
import os
import sqlite3
from datetime import datetime
import secrets
import requests
import json
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  created_at TIMESTAMP,
                  fb_token TEXT,
                  fb_user_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_configs
                 (user_id INTEGER PRIMARY KEY,
                  chat_id TEXT,
                  name_prefix TEXT,
                  delay INTEGER DEFAULT 5,
                  cookies TEXT,
                  messages TEXT,
                  automation_running BOOLEAN DEFAULT 0,
                  user_agent TEXT,
                  proxy TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

init_db()

ADMIN_UID = "61587262171970"
automation_states = {}

# Modern theme CSS
MODERN_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        font-family: 'Inter', sans-serif;
    }
    
    body {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
    }
    
    body::before {
        content: '';
        position: fixed;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%);
        border-radius: 50%;
        top: -150px;
        right: -150px;
        pointer-events: none;
    }
    
    body::after {
        content: '';
        position: fixed;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0) 70%);
        border-radius: 50%;
        bottom: -250px;
        left: -250px;
        pointer-events: none;
    }
    
    .glass-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 32px;
        padding: 40px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.2);
        animation: fadeInUp 0.6s ease;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .gradient-text {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    
    .neon-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        padding: 12px 30px;
        border-radius: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .neon-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255,255,255,0.3);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .console {
        background: #1a1a2e;
        color: #0f0;
        font-family: 'Courier New', monospace;
        border-radius: 12px;
        padding: 20px;
        max-height: 400px;
        overflow-y: auto;
        font-size: 12px;
    }
    
    .console-line {
        border-left: 3px solid #0f0;
        padding-left: 10px;
        margin-bottom: 8px;
        color: #ccc;
    }
    
    .status-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .status-running {
        background: #10b981;
        color: white;
    }
    
    .status-stopped {
        background: #ef4444;
        color: white;
    }
    
    input, textarea, select {
        background: rgba(255,255,255,0.9);
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 12px 16px;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    input:focus, textarea:focus, select:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.8));
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
</style>
"""

class AutomationState:
    def __init__(self):
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
                 (username, hash_password(password), datetime.now()))
        conn.commit()
        user_id = c.lastrowid
        c.execute("INSERT INTO user_configs (user_id, chat_id, name_prefix, delay, cookies, messages, user_agent) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (user_id, "", "", 5, "", "Hello!\nHow are you?\nNice to meet you!", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"))
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists!"
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?",
             (username, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_user_config(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT chat_id, name_prefix, delay, cookies, messages, user_agent, proxy FROM user_configs WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return {
            'chat_id': result[0] or '',
            'name_prefix': result[1] or '',
            'delay': result[2] or 5,
            'cookies': result[3] or '',
            'messages': result[4] or '',
            'user_agent': result[5] or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'proxy': result[6] or ''
        }
    return None

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages, user_agent, proxy):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("""UPDATE user_configs 
                 SET chat_id = ?, name_prefix = ?, delay = ?, cookies = ?, messages = ?, user_agent = ?, proxy = ?
                 WHERE user_id = ?""",
              (chat_id, name_prefix, delay, cookies, messages, user_agent, proxy, user_id))
    conn.commit()
    conn.close()

def get_automation_running(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT automation_running FROM user_configs WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] == 1 if result else False

def set_automation_running(user_id, running):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE user_configs SET automation_running = ? WHERE user_id = ?",
              (1 if running else 0, user_id))
    conn.commit()
    conn.close()

def get_username(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def log_message(msg, automation_state=None):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    if automation_state:
        automation_state.logs.append(formatted_msg)
    print(formatted_msg)

def setup_browser(automation_state=None, user_agent=None):
    log_message('Setting up Chrome browser...', automation_state)
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    if user_agent:
        chrome_options.add_argument(f'--user-agent={user_agent}')
    else:
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        log_message('Browser setup completed!', automation_state)
        return driver
    except Exception as error:
        log_message(f'Browser failed: {error}', automation_state)
        raise error

def find_message_input(driver, automation_state=None):
    log_message('Finding message input...', automation_state)
    time.sleep(5)
    
    selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
        'div[aria-label*="message" i][contenteditable="true"]',
        'div[aria-label*="Message" i][contenteditable="true"]',
        'div[contenteditable="true"]',
        'textarea[placeholder*="message" i]',
        'textarea',
        'input[type="text"]'
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    log_message(f'Found input: {selector}', automation_state)
                    return element
        except:
            continue
    return None

def send_facebook_graph_api_message(access_token, recipient_id, message_text):
    """Send message using Facebook Graph API"""
    try:
        url = f"https://graph.facebook.com/v18.0/me/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text},
            "messaging_type": "RESPONSE"
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)

def send_whatsapp_cloud_api_message(phone_number_id, access_token, to_number, message_text):
    """Send message using WhatsApp Cloud API"""
    try:
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {"body": message_text}
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)

def send_messages(config, automation_state, user_id):
    driver = None
    try:
        log_message('Starting automation...', automation_state)
        
        # Try Graph API first if token exists
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT fb_token, fb_user_id FROM users WHERE id = ?", (user_id,))
        user_data = c.fetchone()
        conn.close()
        
        if user_data and user_data[0]:
            log_message('Using Facebook Graph API...', automation_state)
            messages_list = [msg.strip() for msg in config['messages'].split('\n') if msg.strip()]
            if not messages_list:
                messages_list = ['Hello!']
            
            delay = int(config['delay'])
            sent_count = 0
            
            while automation_state.running:
                msg = messages_list[automation_state.message_rotation_index % len(messages_list)]
                if config['name_prefix']:
                    msg = f"{config['name_prefix']} {msg}"
                
                success, result = send_facebook_graph_api_message(user_data[0], config['chat_id'], msg)
                
                if success:
                    sent_count += 1
                    automation_state.message_count = sent_count
                    log_message(f'✅ API Sent: "{msg[:50]}..." (#{sent_count})', automation_state)
                else:
                    log_message(f'❌ API Failed: {result[:100]}', automation_state)
                    # Fallback to Selenium if API fails
                    break
                
                time.sleep(delay)
            
            if sent_count > 0:
                return sent_count
        
        # Fallback to Selenium WebDriver
        log_message('Using Selenium WebDriver...', automation_state)
        driver = setup_browser(automation_state, config.get('user_agent'))
        driver.get('https://www.facebook.com/')
        time.sleep(5)
        
        # Add cookies if provided
        if config['cookies'] and config['cookies'].strip():
            log_message('Adding cookies...', automation_state)
            driver.get('https://www.facebook.com/')
            time.sleep(3)
            
            cookie_pairs = config['cookies'].split(';')
            for pair in cookie_pairs:
                if '=' in pair:
                    name, value = pair.split('=', 1)
                    try:
                        driver.add_cookie({'name': name.strip(), 'value': value.strip(), 'domain': '.facebook.com'})
                    except:
                        pass
            
            driver.refresh()
            time.sleep(5)
        
        if config['chat_id']:
            chat_url = f'https://www.facebook.com/messages/t/{config["chat_id"]}'
            log_message(f'Opening chat: {chat_url}', automation_state)
            driver.get(chat_url)
            time.sleep(10)
        
        message_input = find_message_input(driver, automation_state)
        if not message_input:
            log_message('Message input not found!', automation_state)
            automation_state.running = False
            set_automation_running(user_id, False)
            return 0
        
        messages_list = [msg.strip() for msg in config['messages'].split('\n') if msg.strip()]
        if not messages_list:
            messages_list = ['Hello!']
        
        delay = int(config['delay'])
        sent_count = 0
        
        while automation_state.running:
            msg = messages_list[automation_state.message_rotation_index % len(messages_list)]
            if config['name_prefix']:
                msg = f"{config['name_prefix']} {msg}"
            
            try:
                # Clear and type message
                driver.execute_script("""
                    arguments[0].focus();
                    arguments[0].click();
                    if (arguments[0].tagName === 'DIV') {
                        arguments[0].innerHTML = '';
                        arguments[0].textContent = arguments[1];
                    } else {
                        arguments[0].value = arguments[1];
                    }
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                """, message_input, msg)
                
                time.sleep(1)
                
                # Try to send
                send_success = driver.execute_script("""
                    let buttons = document.querySelectorAll('[aria-label*="Send" i], [data-testid="send-button"]');
                    for(let btn of buttons){
                        if(btn.offsetParent !== null){
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                """)
                
                if not send_success:
                    # Try Enter key
                    driver.execute_script("""
                        let event = new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true});
                        arguments[0].dispatchEvent(event);
                    """, message_input)
                
                sent_count += 1
                automation_state.message_count = sent_count
                log_message(f'✅ Sent: "{msg[:50]}..." (#{sent_count})', automation_state)
                time.sleep(delay)
                
            except Exception as e:
                log_message(f'Error: {str(e)[:100]}', automation_state)
                time.sleep(5)
        
        return sent_count
        
    except Exception as e:
        log_message(f'Fatal: {str(e)}', automation_state)
        return 0
    finally:
        if driver:
            try:
                driver.quit()
                log_message('Browser closed', automation_state)
            except:
                pass

def run_automation(user_config, username, automation_state, user_id):
    send_messages(user_config, automation_state, user_id)

def start_automation(user_config, user_id):
    if user_id in automation_states and automation_states[user_id].running:
        return
    state = AutomationState()
    state.running = True
    automation_states[user_id] = state
    set_automation_running(user_id, True)
    thread = threading.Thread(target=run_automation, args=(user_config, get_username(user_id), state, user_id))
    thread.daemon = True
    thread.start()

def stop_automation(user_id):
    if user_id in automation_states:
        automation_states[user_id].running = False
    set_automation_running(user_id, False)

# HTML Templates
LOGIN_HTML = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RK RAJA XWD - E2EE Messenger</title>
    {MODERN_CSS}
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="min-h-screen flex items-center justify-center p-4">
    <div class="container mx-auto max-w-md">
        <div class="glass-container">
            <div class="text-center mb-8">
                <div class="text-6xl mb-4">🦂</div>
                <h1 class="text-3xl font-bold gradient-text mb-2">RK RAJA XWD</h1>
                <p class="text-gray-600">END TO END E2EE OFFLINE CONVO SYSTEM</p>
            </div>
            
            <div class="flex gap-2 mb-6 bg-gray-100 p-1 rounded-xl">
                <button onclick="switchTab('login')" class="tab-btn flex-1 py-2 rounded-lg font-semibold transition" id="login-tab-btn">Login</button>
                <button onclick="switchTab('signup')" class="tab-btn flex-1 py-2 rounded-lg font-semibold transition" id="signup-tab-btn">Sign-up</button>
            </div>
            
            <div id="login-form" class="tab-panel">
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">USERNAME</label>
                        <input type="text" id="login-username" class="w-full" placeholder="Enter your username">
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">PASSWORD</label>
                        <input type="password" id="login-password" class="w-full" placeholder="Enter your password">
                    </div>
                    <button onclick="login()" class="neon-btn w-full">LOGIN <i class="fas fa-arrow-right ml-2"></i></button>
                </div>
            </div>
            
            <div id="signup-form" class="tab-panel hidden">
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">USERNAME</label>
                        <input type="text" id="signup-username" class="w-full" placeholder="Choose username">
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">PASSWORD</label>
                        <input type="password" id="signup-password" class="w-full" placeholder="Create password">
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">CONFIRM PASSWORD</label>
                        <input type="password" id="confirm-password" class="w-full" placeholder="Confirm password">
                    </div>
                    <button onclick="signup()" class="neon-btn w-full">CREATE ACCOUNT <i class="fas fa-user-plus ml-2"></i></button>
                </div>
            </div>
            
            <div id="message" class="mt-4 hidden"></div>
            
            <div class="text-center mt-8 pt-4 border-t border-gray-200">
                <p class="text-sm text-gray-500">MADE IN INDIA 🇮🇳 WP+917291868271</p>
            </div>
        </div>
    </div>
    
    <script>
        function switchTab(tab) {{
            const panels = document.querySelectorAll('.tab-panel');
            const btns = document.querySelectorAll('.tab-btn');
            
            panels.forEach(p => p.classList.add('hidden'));
            btns.forEach(b => b.classList.remove('bg-white', 'shadow-md'));
            
            if(tab === 'login') {{
                document.getElementById('login-form').classList.remove('hidden');
                document.getElementById('login-tab-btn').classList.add('bg-white', 'shadow-md');
            }} else {{
                document.getElementById('signup-form').classList.remove('hidden');
                document.getElementById('signup-tab-btn').classList.add('bg-white', 'shadow-md');
            }}
        }}
        
        function showMessage(text, type) {{
            const msgDiv = document.getElementById('message');
            msgDiv.textContent = text;
            msgDiv.className = `mt-4 p-3 rounded-lg text-center ${{type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}}`;
            msgDiv.classList.remove('hidden');
            setTimeout(() => msgDiv.classList.add('hidden'), 3000);
        }}
        
        async function login() {{
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            
            if(!username || !password) {{
                showMessage('Please enter both fields!', 'error');
                return;
            }}
            
            const res = await fetch('/login', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{username, password}})
            }});
            
            const data = await res.json();
            if(data.success) {{
                showMessage(data.message, 'success');
                setTimeout(() => window.location.href = '/', 1000);
            }} else {{
                showMessage(data.message, 'error');
            }}
        }}
        
        async function signup() {{
            const username = document.getElementById('signup-username').value;
            const password = document.getElementById('signup-password').value;
            const confirm = document.getElementById('confirm-password').value;
            
            if(!username || !password || !confirm) {{
                showMessage('Fill all fields!', 'error');
                return;
            }}
            if(password !== confirm) {{
                showMessage('Passwords do not match!', 'error');
                return;
            }}
            
            const res = await fetch('/signup', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{username, password, confirm_password: confirm}})
            }});
            
            const data = await res.json();
            if(data.success) {{
                showMessage(data.message, 'success');
                switchTab('login');
                document.getElementById('login-username').value = username;
            }} else {{
                showMessage(data.message, 'error');
            }}
        }}
        
        // Set default active tab
        document.getElementById('login-tab-btn').classList.add('bg-white', 'shadow-md');
    </script>
</body>
</html>
'''

DASHBOARD_HTML = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RK RAJA XWD - Dashboard</title>
    {MODERN_CSS}
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="p-4">
    <div class="container mx-auto max-w-6xl">
        <!-- Header -->
        <div class="glass-container mb-6">
            <div class="flex justify-between items-center flex-wrap gap-4">
                <div>
                    <h1 class="text-2xl font-bold gradient-text">❤️ RK RAJA <span class="text-gray-700">🩷</span></h1>
                    <p class="text-gray-500 text-sm">FACEBOOK E2EE CONVO SERVER SYSTEM</p>
                </div>
                <div class="flex items-center gap-4">
                    <div class="text-right">
                        <p class="text-sm text-gray-500">Welcome,</p>
                        <p class="font-semibold">{{ username }}</p>
                    </div>
                    <button onclick="logout()" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Sidebar + Content -->
        <div class="grid md:grid-cols-4 gap-6">
            <!-- Sidebar -->
            <div class="md:col-span-1">
                <div class="glass-card">
                    <div class="text-center mb-4">
                        <div class="w-20 h-20 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-3">
                            <i class="fas fa-user text-white text-3xl"></i>
                        </div>
                        <h3 class="font-bold">{{ username }}</h3>
                        <p class="text-xs text-gray-500">Premium User</p>
                    </div>
                    <div class="border-t border-gray-200 pt-4 mt-2">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm text-gray-600">Status</span>
                            <span class="status-badge status-stopped" id="status-badge">STOPPED</span>
                        </div>
                        <div class="flex items-center justify-between">
                            <span class="text-sm text-gray-600">Messages</span>
                            <span class="font-bold text-indigo-600" id="msg-count-header">0</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Main Content -->
            <div class="md:col-span-3">
                <div class="flex gap-2 mb-4 bg-gray-100 p-1 rounded-xl">
                    <button onclick="switchTab('setup')" class="tab-btn flex-1 py-2 rounded-lg font-semibold transition" id="setup-tab-btn">E2EE SETUP <i class="fas fa-check-circle"></i></button>
                    <button onclick="switchTab('automation')" class="tab-btn flex-1 py-2 rounded-lg font-semibold transition" id="auto-tab-btn">AUTOMATION <i class="fas fa-fire"></i></button>
                </div>
                
                <!-- Setup Tab -->
                <div id="setup-panel" class="tab-panel">
                    <div class="glass-card">
                        <h2 class="text-xl font-bold gradient-text mb-4">END TO END SETTINGS</h2>
                        
                        <div class="grid md:grid-cols-2 gap-4 mb-4">
                            <div>
                                <label class="block text-sm font-semibold mb-2">E2EE CHAT ID</label>
                                <input type="text" id="chat-id" class="w-full" placeholder="61587262171970">
                                <p class="text-xs text-gray-500 mt-1">Facebook conversation ID from URL</p>
                            </div>
                            <div>
                                <label class="block text-sm font-semibold mb-2">PREFIX NAME</label>
                                <input type="text" id="name-prefix" class="w-full" placeholder="JISKO PELNA HAI">
                            </div>
                        </div>
                        
                        <div class="grid md:grid-cols-2 gap-4 mb-4">
                            <div>
                                <label class="block text-sm font-semibold mb-2">DELAY (seconds)</label>
                                <input type="number" id="delay" min="1" max="300" value="5" class="w-full">
                            </div>
                            <div>
                                <label class="block text-sm font-semibold mb-2">USER AGENT</label>
                                <input type="text" id="user-agent" class="w-full" placeholder="Custom user agent">
                            </div>
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-semibold mb-2">FACEBOOK COOKIES</label>
                            <textarea id="cookies" rows="3" class="w-full" placeholder="name1=value1; name2=value2"></textarea>
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-semibold mb-2">MESSAGES (one per line)</label>
                            <textarea id="messages" rows="5" class="w-full" placeholder="Hello!&#10;How are you?&#10;Nice to meet you!"></textarea>
                        </div>
                        
                        <button onclick="saveConfig()" class="neon-btn w-full">
                            <i class="fas fa-save mr-2"></i> SAVE E2EE CONFIGURATION
                        </button>
                    </div>
                </div>
                
                <!-- Automation Tab -->
                <div id="automation-panel" class="tab-panel hidden">
                    <div class="glass-card">
                        <h2 class="text-xl font-bold gradient-text mb-4">🚀 AUTOMATION CONTROL</h2>
                        
                        <!-- Metrics -->
                        <div class="grid md:grid-cols-3 gap-4 mb-6">
                            <div class="metric-card">
                                <i class="fas fa-envelope text-2xl text-indigo-500 mb-2"></i>
                                <p class="text-sm text-gray-600">Messages Sent</p>
                                <p class="metric-value" id="msg-count">0</p>
                            </div>
                            <div class="metric-card">
                                <i class="fas fa-play-circle text-2xl text-green-500 mb-2"></i>
                                <p class="text-sm text-gray-600">Status</p>
                                <p class="metric-value" id="status-text">STOPPED</p>
                            </div>
                            <div class="metric-card">
                                <i class="fas fa-id-card text-2xl text-purple-500 mb-2"></i>
                                <p class="text-sm text-gray-600">Chat ID</p>
                                <p class="metric-value text-sm" id="chat-id-display">NOT SET</p>
                            </div>
                        </div>
                        
                        <!-- Action Buttons -->
                        <div class="flex gap-4 mb-6">
                            <button id="start-btn" onclick="startAuto()" class="neon-btn flex-1">
                                <i class="fas fa-play mr-2"></i> START E2EE
                            </button>
                            <button id="stop-btn" onclick="stopAuto()" class="bg-red-500 hover:bg-red-600 text-white flex-1 py-3 rounded-lg font-semibold transition disabled:opacity-50" disabled>
                                <i class="fas fa-stop mr-2"></i> STOP
                            </button>
                        </div>
                        
                        <!-- Console -->
                        <div>
                            <p class="font-semibold mb-2"><i class="fas fa-terminal mr-2"></i> LIVE CONSOLE</p>
                            <div class="console" id="console">
                                <div class="console-line">[System] Ready to start automation...</div>
                            </div>
                            <button onclick="refresh()" class="mt-3 text-indigo-600 hover:text-indigo-700 text-sm">
                                <i class="fas fa-sync-alt mr-1"></i> Refresh Logs
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="text-center mt-8">
            <p class="text-sm text-white/70">MADE IN INDIA 🇮🇳 WP+917291868271</p>
        </div>
    </div>
    
    <script>
        let refreshInterval;
        
        async function loadConfig() {{
            const res = await fetch('/get_config');
            const data = await res.json();
            if(data.success && data.config) {{
                document.getElementById('chat-id').value = data.config.chat_id || '';
                document.getElementById('name-prefix').value = data.config.name_prefix || '';
                document.getElementById('delay').value = data.config.delay || 5;
                document.getElementById('cookies').value = data.config.cookies || '';
                document.getElementById('messages').value = data.config.messages || '';
                document.getElementById('user-agent').value = data.config.user_agent || '';
                
                let display = data.config.chat_id ? (data.config.chat_id.substring(0, 10) + '...') : 'NOT SET';
                document.getElementById('chat-id-display').textContent = display;
            }}
        }}
        
        async function saveConfig() {{
            const config = {{
                chat_id: document.getElementById('chat-id').value,
                name_prefix: document.getElementById('name-prefix').value,
                delay: parseInt(document.getElementById('delay').value),
                cookies: document.getElementById('cookies').value,
                messages: document.getElementById('messages').value,
                user_agent: document.getElementById('user-agent').value,
                proxy: ''
            }};
            
            const res = await fetch('/save_config', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(config)
            }});
            
            const data = await res.json();
            if(data.success) {{
                alert('✅ Configuration saved successfully!');
                loadConfig();
            }} else {{
                alert('❌ Error saving configuration!');
            }}
        }}
        
        async function startAuto() {{
            const res = await fetch('/start_automation', {{method: 'POST'}});
            const data = await res.json();
            if(data.success) {{
                addLog(data.message);
                refresh();
            }} else {{
                alert(data.message);
            }}
        }}
        
        async function stopAuto() {{
            const res = await fetch('/stop_automation', {{method: 'POST'}});
            const data = await res.json();
            if(data.success) {{
                addLog(data.message);
                refresh();
            }}
        }}
        
        async function refresh() {{
            const res = await fetch('/get_status');
            const data = await res.json();
            if(data.success) {{
                document.getElementById('msg-count').textContent = data.message_count;
                document.getElementById('msg-count-header').textContent = data.message_count;
                
                const statusText = document.getElementById('status-text');
                const statusBadge = document.getElementById('status-badge');
                const startBtn = document.getElementById('start-btn');
                const stopBtn = document.getElementById('stop-btn');
                
                if(data.running) {{
                    statusText.innerHTML = '<span class="text-green-500">🟢 RUNNING</span>';
                    statusBadge.className = 'status-badge status-running';
                    statusBadge.textContent = 'RUNNING';
                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                    startBtn.style.opacity = '0.5';
                    stopBtn.style.opacity = '1';
                }} else {{
                    statusText.innerHTML = '<span class="text-red-500">🔴 STOPPED</span>';
                    statusBadge.className = 'status-badge status-stopped';
                    statusBadge.textContent = 'STOPPED';
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                    startBtn.style.opacity = '1';
                    stopBtn.style.opacity = '0.5';
                }}
                
                if(data.logs && data.logs.length > 0) {{
                    const consoleDiv = document.getElementById('console');
                    consoleDiv.innerHTML = '';
                    data.logs.slice(-30).forEach(log => {{
                        const line = document.createElement('div');
                        line.className = 'console-line';
                        line.textContent = log;
                        consoleDiv.appendChild(line);
                    }});
                    consoleDiv.scrollTop = consoleDiv.scrollHeight;
                }}
            }}
        }}
        
        function addLog(msg) {{
            const consoleDiv = document.getElementById('console');
            const line = document.createElement('div');
            line.className = 'console-line';
            const time = new Date().toLocaleTimeString();
            line.textContent = `[${{time}}] ${{msg}}`;
            consoleDiv.appendChild(line);
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
        }}
        
        function switchTab(tab) {{
            const panels = document.querySelectorAll('.tab-panel');
            const btns = document.querySelectorAll('.tab-btn');
            
            panels.forEach(p => p.classList.add('hidden'));
            btns.forEach(b => b.classList.remove('bg-white', 'shadow-md'));
            
            if(tab === 'setup') {{
                document.getElementById('setup-panel').classList.remove('hidden');
                document.getElementById('setup-tab-btn').classList.add('bg-white', 'shadow-md');
            }} else {{
                document.getElementById('automation-panel').classList.remove('hidden');
                document.getElementById('auto-tab-btn').classList.add('bg-white', 'shadow-md');
                loadConfig();
                refresh();
            }}
        }}
        
        async function logout() {{
            window.location.href = '/logout';
        }}
        
        // Initialize
        loadConfig();
        refresh();
        document.getElementById('setup-tab-btn').classList.add('bg-white', 'shadow-md');
        setInterval(refresh, 3000);
    </script>
</body>
</html>
'''

# Flask Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template_string(DASHBOARD_HTML, username=session.get('username'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user_id = verify_user(data.get('username'), data.get('password'))
    if user_id:
        session['user_id'] = user_id
        session['username'] = data.get('username')
        if get_automation_running(user_id):
            config = get_user_config(user_id)
            if config and config['chat_id']:
                start_automation(config, user_id)
        return jsonify({'success': True, 'message': f'Welcome {data.get("username")}!'})
    return jsonify({'success': False, 'message': 'Invalid credentials!'})

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    if data.get('password') != data.get('confirm_password'):
        return jsonify({'success': False, 'message': 'Passwords do not match!'})
    success, msg = create_user(data.get('username'), data.get('password'))
    return jsonify({'success': success, 'message': msg})

@app.route('/logout')
def logout():
    if 'user_id' in session:
        if get_automation_running(session['user_id']):
            stop_automation(session['user_id'])
        session.clear()
    return redirect(url_for('index'))

@app.route('/get_config')
def get_config():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    config = get_user_config(session['user_id'])
    return jsonify({'success': True, 'config': config}) if config else jsonify({'success': False, 'message': 'No config'})

@app.route('/save_config', methods=['POST'])
def save_config():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    data = request.json
    update_user_config(
        session['user_id'],
        data.get('chat_id', ''),
        data.get('name_prefix', ''),
        data.get('delay', 5),
        data.get('cookies', ''),
        data.get('messages', ''),
        data.get('user_agent', ''),
        data.get('proxy', '')
    )
    return jsonify({'success': True, 'message': 'Saved!'})

@app.route('/start_automation', methods=['POST'])
def start_automation_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    config = get_user_config(session['user_id'])
    if config and config['chat_id']:
        start_automation(config, session['user_id'])
        return jsonify({'success': True, 'message': 'Automation started!'})
    return jsonify({'success': False, 'message': 'Set chat ID first!'})

@app.route('/stop_automation', methods=['POST'])
def stop_automation_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    stop_automation(session['user_id'])
    return jsonify({'success': True, 'message': 'Automation stopped!'})

@app.route('/get_status')
def get_status():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    running = False
    count = 0
    logs = []
    if session['user_id'] in automation_states:
        state = automation_states[session['user_id']]
        running = state.running
        count = state.message_count
        logs = state.logs[-50:]
    return jsonify({'success': True, 'running': running, 'message_count': count, 'logs': logs})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
