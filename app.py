from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import time
import threading
import hashlib
import os
import sqlite3
from datetime import datetime
import secrets
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ============ DATABASE SETUP ============
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  created_at TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_configs
                 (user_id INTEGER PRIMARY KEY,
                  chat_id TEXT,
                  name_prefix TEXT,
                  delay INTEGER DEFAULT 5,
                  cookies TEXT,
                  messages TEXT,
                  automation_running BOOLEAN DEFAULT 0,
                  admin_e2ee_thread_id TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

init_db()

ADMIN_UID = "61587262171970"
automation_states = {}

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
        c.execute("INSERT INTO user_configs (user_id, chat_id, name_prefix, delay, cookies, messages) VALUES (?, ?, ?, ?, ?, ?)",
                 (user_id, "", "", 5, "", "Hello!\nHow are you?\nNice to meet you!"))
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
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("""UPDATE user_configs 
                 SET chat_id = ?, name_prefix = ?, delay = ?, cookies = ?, messages = ?
                 WHERE user_id = ?""",
              (chat_id, name_prefix, delay, cookies, messages, user_id))
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

def setup_browser(automation_state=None):
    log_message('Setting up Chrome browser...', automation_state)
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
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
        'div[contenteditable="true"]',
        'textarea',
        'input[type="text"]'
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed():
                    log_message(f'Found input: {selector}', automation_state)
                    return element
        except:
            continue
    return None

def send_messages(config, automation_state, user_id):
    driver = None
    try:
        log_message('Starting automation...', automation_state)
        driver = setup_browser(automation_state)
        driver.get('https://www.facebook.com/')
        time.sleep(5)
        
        if config['chat_id']:
            driver.get(f'https://www.facebook.com/messages/t/{config["chat_id"]}')
            time.sleep(8)
        
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
                driver.execute_script("""
                    arguments[0].focus();
                    arguments[0].click();
                    arguments[0].innerHTML = arguments[1];
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                """, message_input, msg)
                
                time.sleep(1)
                driver.execute_script("""
                    let btns = document.querySelectorAll('[aria-label*="Send" i]');
                    for(let btn of btns){
                        if(btn.offsetParent){ btn.click(); break; }
                    }
                """)
                
                sent_count += 1
                automation_state.message_count = sent_count
                log_message(f'✅ Sent: "{msg[:30]}..." (#{sent_count})', automation_state)
                time.sleep(delay)
                
            except Exception as e:
                log_message(f'Error: {str(e)[:50]}', automation_state)
                time.sleep(5)
        
        return sent_count
    except Exception as e:
        log_message(f'Fatal: {str(e)}', automation_state)
        return 0
    finally:
        if driver:
            driver.quit()

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

# ============ HTML TEMPLATES ============
LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RK RAJA XWD - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background: linear-gradient(136deg, #f6f9ff 0%, #e9f3ff 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { background: rgba(255,255,255,0.95); border-radius: 28px; padding: 40px; max-width: 500px; width: 100%; box-shadow: 0 10px 40px rgba(0,0,0,0.08); }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #0077ff; font-size: 2rem; }
        .header p { color: #005fcc; }
        .tabs { display: flex; gap: 10px; margin-bottom: 30px; background: #f4f9ff; padding: 8px; border-radius: 16px; }
        .tab { flex: 1; padding: 12px; text-align: center; cursor: pointer; border-radius: 12px; font-weight: 600; color: #0077ff; }
        .tab.active { background: #0077ff; color: white; }
        .form-group { margin-bottom: 20px; }
        label { color: #006be8; font-weight: 700; display: block; margin-bottom: 8px; }
        input { width: 100%; padding: 14px; border: 1.5px solid #cfe4ff; border-radius: 12px; font-size: 1rem; background: white; }
        input:focus { outline: none; border-color: #0078ff; }
        button { width: 100%; padding: 1rem; background: linear-gradient(140deg, #009dff, #006bff); color: white; font-weight: 700; border: none; border-radius: 14px; cursor: pointer; }
        button:hover { transform: translateY(-2px); }
        .message { margin-top: 20px; padding: 12px; border-radius: 12px; text-align: center; display: none; }
        .message.success { background: #c7ffea; color: #007f5b; display: block; }
        .message.error { background: #ffe1e1; color: #b10000; display: block; }
        .footer { text-align: center; margin-top: 30px; color: #0077ff; font-weight: 800; }
        .form { display: none; }
        .form.active { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>🦂 RK RAJA XWD</h1><p>END TO END (E2EE) OFFLINE CONVO SYSTEM</p></div>
        <div class="tabs"><div class="tab active" onclick="switchTab('login')">Login</div><div class="tab" onclick="switchTab('signup')">Sign-up</div></div>
        <div id="login-form" class="form active">
            <div class="form-group"><label>USERNAME</label><input type="text" id="login-username" placeholder="Enter username"></div>
            <div class="form-group"><label>PASSWORD</label><input type="password" id="login-password" placeholder="Enter password"></div>
            <button onclick="login()">LOGIN</button>
        </div>
        <div id="signup-form" class="form">
            <div class="form-group"><label>USERNAME</label><input type="text" id="signup-username" placeholder="Choose username"></div>
            <div class="form-group"><label>PASSWORD</label><input type="password" id="signup-password" placeholder="Create password"></div>
            <div class="form-group"><label>CONFIRM PASSWORD</label><input type="password" id="confirm-password" placeholder="Confirm password"></div>
            <button onclick="signup()">CREATE ACCOUNT</button>
        </div>
        <div id="message" class="message"></div>
        <div class="footer">MADE IN INDIA 🇮🇳 WP+917291868271</div>
    </div>
    <script>
        function switchTab(tab){
            document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
            document.querySelectorAll('.form').forEach(f=>f.classList.remove('active'));
            if(tab==='login'){ document.querySelector('.tab:first-child').classList.add('active'); document.getElementById('login-form').classList.add('active'); }
            else{ document.querySelector('.tab:last-child').classList.add('active'); document.getElementById('signup-form').classList.add('active'); }
            document.getElementById('message').style.display='none';
        }
        function showMessage(text,type){
            const msg=document.getElementById('message');
            msg.textContent=text; msg.className='message '+type;
            setTimeout(()=>msg.style.display='none',3000);
        }
        async function login(){
            const username=document.getElementById('login-username').value;
            const password=document.getElementById('login-password').value;
            if(!username||!password){ showMessage('Please enter both!','error'); return; }
            const res=await fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})});
            const data=await res.json();
            if(data.success){ showMessage(data.message,'success'); setTimeout(()=>window.location.href='/',1000); }
            else{ showMessage(data.message,'error'); }
        }
        async function signup(){
            const username=document.getElementById('signup-username').value;
            const password=document.getElementById('signup-password').value;
            const confirm=document.getElementById('confirm-password').value;
            if(!username||!password||!confirm){ showMessage('Fill all fields!','error'); return; }
            if(password!==confirm){ showMessage('Passwords do not match!','error'); return; }
            const res=await fetch('/signup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password,confirm_password:confirm})});
            const data=await res.json();
            if(data.success){ showMessage(data.message,'success'); switchTab('login'); document.getElementById('login-username').value=username; }
            else{ showMessage(data.message,'error'); }
        }
    </script>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RK RAJA XWD - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background: linear-gradient(136deg, #f6f9ff 0%, #e9f3ff 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #ffffff, #f0f8ff); border-radius: 25px; padding: 30px; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,140,255,0.12); }
        .header h1 { color: #0077ff; font-size: 2rem; }
        .sidebar { background: rgba(255,255,255,0.95); border-radius: 25px; padding: 20px; margin-bottom: 20px; }
        .sidebar-header { font-size: 1.2rem; font-weight: 800; color: #0077ff; margin-bottom: 15px; border-bottom: 2px solid #cfe4ff; padding-bottom: 10px; }
        .user-info { padding: 10px; background: #f4f9ff; border-radius: 12px; margin-bottom: 15px; }
        .premium-badge { background: linear-gradient(135deg, #c7ffea, #9dffe0); border-radius: 12px; padding: 12px; text-align: center; color: #007f5b; font-weight: 700; margin-bottom: 15px; }
        .logout-btn { width: 100%; padding: 12px; background: linear-gradient(140deg, #ff6b6b, #ff4444); color: white; font-weight: 700; border: none; border-radius: 12px; cursor: pointer; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; background: #ffffff; padding: 8px; border-radius: 16px; }
        .tab { flex: 1; padding: 12px; text-align: center; cursor: pointer; border-radius: 12px; font-weight: 600; background: #f4f9ff; color: #0077ff; }
        .tab.active { background: #0077ff; color: white; }
        .content { background: rgba(255,255,255,0.95); border-radius: 25px; padding: 30px; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .form-group { margin-bottom: 20px; }
        label { color: #006be8; font-weight: 700; display: block; margin-bottom: 8px; }
        input, textarea { width: 100%; padding: 14px; border: 1.5px solid #cfe4ff; border-radius: 12px; font-size: 1rem; background: white; }
        textarea { min-height: 150px; resize: vertical; }
        button { padding: 1rem 2rem; background: linear-gradient(140deg, #009dff, #006bff); color: white; font-weight: 700; border: none; border-radius: 14px; cursor: pointer; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: linear-gradient(135deg, #ffffff, #f4f9ff); border-radius: 16px; padding: 20px; text-align: center; }
        .metric-label { color: #006be8; font-weight: 600; margin-bottom: 10px; }
        .metric-value { font-size: 1.8rem; font-weight: 800; color: #0077ff; }
        .console-output { background: #ffffff; border: 2px solid #b7d9ff; border-radius: 15px; padding: 20px; max-height: 400px; overflow-y: auto; margin-top: 20px; }
        .console-line { background: #eef6ff; padding: 10px; border-left: 4px solid #0077ff; border-radius: 6px; margin-bottom: 8px; font-family: monospace; }
        .action-buttons { display: flex; gap: 10px; margin-top: 20px; }
        .action-buttons button { flex: 1; }
        .footer { text-align: center; margin-top: 30px; color: #0077ff; font-weight: 800; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>❤️ RK RAJA 🩷</h1><p>FACEBOOK E2EE CONVO SERVER SYSTEM</p></div>
        <div class="sidebar">
            <div class="sidebar-header">👤 USER DASHBOARD</div>
            <div class="user-info"><strong>USERNAME:</strong> <span id="username">{{ username }}</span></div>
            <div class="premium-badge">✅ PREMIUM ACCESS</div>
            <button class="logout-btn" onclick="logout()">🚪 LOGOUT</button>
        </div>
        <div class="tabs"><div class="tab active" onclick="switchTab('setup')">E2EE SET-UP ✅</div><div class="tab" onclick="switchTab('automation')">🔥 AUTOMATION</div></div>
        <div class="content">
            <div id="setup-tab" class="tab-content active">
                <h2 style="color:#0077ff; margin-bottom:20px;">END TO END SETTINGS</h2>
                <div class="grid-2">
                    <div><div class="form-group"><label>PASTE E2EE ID</label><input type="text" id="chat-id" placeholder="61587262171970"></div>
                    <div class="form-group"><label>HATERS NAME</label><input type="text" id="name-prefix" placeholder="JISKO PELNA HAI USKA NAME"></div>
                    <div class="form-group"><label>DELAY (SECONDS)</label><input type="number" id="delay" min="1" max="300" value="5"></div></div>
                    <div><div class="form-group"><label>PASTE FACEBOOK COOKIES</label><textarea id="cookies" placeholder="Paste cookies here"></textarea></div></div>
                </div>
                <div class="form-group"><label>TYPE MESSAGE ONE PER LINE</label><textarea id="messages" placeholder="Enter messages here, one per line"></textarea></div>
                <button onclick="saveConfig()">💾 SAVE E2EE</button>
            </div>
            <div id="automation-tab" class="tab-content">
                <h2 style="color:#0077ff; margin-bottom:20px;">🚀 AUTOMATION CONTROL</h2>
                <div class="metrics">
                    <div class="metric-card"><div class="metric-label">MESSAGES SENT</div><div class="metric-value" id="msg-count">0</div></div>
                    <div class="metric-card"><div class="metric-label">STATUS</div><div class="metric-value" id="status">🔴 STOP</div></div>
                    <div class="metric-card"><div class="metric-label">CHAT ID</div><div class="metric-value" id="chat-id-display">NOT SET</div></div>
                </div>
                <div class="action-buttons">
                    <button id="start-btn" onclick="startAuto()">▶️ START E2EE AUTOMATION</button>
                    <button id="stop-btn" onclick="stopAuto()" disabled>⏹️ STOP E2EE AUTOMATION</button>
                </div>
                <div class="console-output" id="console"><div class="console-line">[System] Ready...</div></div>
                <button onclick="refresh()" style="margin-top:10px;">🔄 REFRESH</button>
            </div>
        </div>
        <div class="footer">MADE IN INDIA 🇮🇳 WP+917291868271</div>
    </div>
    <script>
        async function loadConfig(){
            const res=await fetch('/get_config');
            const data=await res.json();
            if(data.success){
                document.getElementById('chat-id').value=data.config.chat_id||'';
                document.getElementById('name-prefix').value=data.config.name_prefix||'';
                document.getElementById('delay').value=data.config.delay||5;
                document.getElementById('cookies').value=data.config.cookies||'';
                document.getElementById('messages').value=data.config.messages||'';
                let display=data.config.chat_id?(data.config.chat_id.substring(0,8)+'...'):'NOT SET';
                document.getElementById('chat-id-display').textContent=display;
            }
        }
        async function saveConfig(){
            const config={
                chat_id:document.getElementById('chat-id').value,
                name_prefix:document.getElementById('name-prefix').value,
                delay:parseInt(document.getElementById('delay').value),
                cookies:document.getElementById('cookies').value,
                messages:document.getElementById('messages').value
            };
            const res=await fetch('/save_config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)});
            const data=await res.json();
            if(data.success){ alert('Configuration saved!'); loadConfig(); }
            else{ alert('Error saving!'); }
        }
        async function startAuto(){
            const res=await fetch('/start_automation',{method:'POST'});
            const data=await res.json();
            if(data.success){ addLog(data.message); refresh(); }
            else{ alert(data.message); }
        }
        async function stopAuto(){
            const res=await fetch('/stop_automation',{method:'POST'});
            const data=await res.json();
            if(data.success){ addLog(data.message); refresh(); }
        }
        async function refresh(){
            const res=await fetch('/get_status');
            const data=await res.json();
            if(data.success){
                document.getElementById('msg-count').textContent=data.message_count;
                if(data.running){ document.getElementById('status').innerHTML='🟢 RUNNING'; document.getElementById('start-btn').disabled=true; document.getElementById('stop-btn').disabled=false; }
                else{ document.getElementById('status').innerHTML='🔴 STOP'; document.getElementById('start-btn').disabled=false; document.getElementById('stop-btn').disabled=true; }
                const consoleDiv=document.getElementById('console');
                if(data.logs&&data.logs.length){
                    consoleDiv.innerHTML='';
                    data.logs.forEach(log=>{ let line=document.createElement('div'); line.className='console-line'; line.textContent=log; consoleDiv.appendChild(line); });
                    consoleDiv.scrollTop=consoleDiv.scrollHeight;
                }
            }
        }
        function addLog(msg){ const consoleDiv=document.getElementById('console'); let line=document.createElement('div'); line.className='console-line'; line.textContent='['+new Date().toLocaleTimeString()+'] '+msg; consoleDiv.appendChild(line); consoleDiv.scrollTop=consoleDiv.scrollHeight; }
        function switchTab(tab){
            document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(tc=>tc.classList.remove('active'));
            if(tab==='setup'){ document.querySelector('.tab:first-child').classList.add('active'); document.getElementById('setup-tab').classList.add('active'); }
            else{ document.querySelector('.tab:last-child').classList.add('active'); document.getElementById('automation-tab').classList.add('active'); loadConfig(); refresh(); }
        }
        function logout(){ window.location.href='/logout'; }
        loadConfig();
        setInterval(refresh,3000);
    </script>
</body>
</html>
'''

# ============ FLASK ROUTES ============
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
    update_user_config(session['user_id'], data.get('chat_id',''), data.get('name_prefix',''), data.get('delay',5), data.get('cookies',''), data.get('messages',''))
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
