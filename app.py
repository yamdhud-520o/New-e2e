# app.py - Main application file for Render deployment

import time
import threading
import uuid
import hashlib
import os
import subprocess
import json
import urllib.parse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import database as db
import requests
import sys

# Flask imports for web interface
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from functools import wraps

# HTML Templates
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦂RK RAJA XWD - E2EE System</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {
            font-family: 'Outfit', sans-serif !important;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(136deg, #f6f9ff 0%, #e9f3ff 40%, #e1f0ff 100%);
            background-attachment: fixed;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.85);
            border-radius: 28px;
            padding: 40px;
            border: 1px solid rgba(0,3,0,0.06);
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            max-width: 500px;
            width: 100%;
            animation: smoothFade 0.5s ease;
        }
        
        @keyframes smoothFade {
            from {opacity: 0; transform: translateY(12px);}
            to {opacity: 1; transform: translateY(0);}
        }
        
        .main-header {
            background: linear-gradient(135deg, #ffffff, #f0f8ff, #e7f3ff);
            border-radius: 25px;
            padding: 30px 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 140, 255, 0.12);
            border: 1px solid rgba(0, 140, 255, 0.15);
            margin-bottom: 30px;
        }
        
        .main-header h1 {
            color: #0077ff;
            font-size: 2rem;
            font-weight: 900;
        }
        
        .main-header p {
            color: #005fcc;
            font-size: 1rem;
            opacity: 0.85;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }
        
        .tab-btn {
            flex: 1;
            background: #f4f9ff;
            border: 1px solid rgba(0,0,0,0.05);
            border-radius: 12px;
            padding: 12px;
            font-weight: 600;
            color: #0077ff;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .tab-btn.active {
            background: #0077ff;
            color: white;
            box-shadow: 0 0 14px rgba(0,100,255,0.4);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: smoothFade 0.3s ease;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            color: #006be8;
            font-weight: 700;
            display: block;
            margin-bottom: 8px;
        }
        
        input {
            width: 100%;
            background: #ffffff;
            border-radius: 12px;
            padding: 14px;
            border: 1.5px solid #cfe4ff;
            color: #333;
            font-size: 1rem;
            transition: 0.2s ease;
            outline: none;
        }
        
        input:focus {
            border-color: #0078ff;
            box-shadow: 0 0 12px rgba(0,120,255,0.3);
        }
        
        button {
            background: linear-gradient(140deg, #009dff 0%, #006bff 100%);
            color: white;
            font-weight: 700;
            font-size: 1.1rem;
            padding: 1rem 2rem;
            border-radius: 14px;
            border: none;
            transition: 0.3s ease;
            box-shadow: 0 10px 20px rgba(0,100,255,0.25);
            cursor: pointer;
            width: 100%;
        }
        
        button:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 28px rgba(0,100,255,0.35);
        }
        
        .alert {
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: 700;
        }
        
        .alert-success {
            background: linear-gradient(135deg, #c7ffea, #9dffe0);
            color: #007f5b;
        }
        
        .alert-error {
            background: linear-gradient(135deg, #ffe1e1, #ffd4d4);
            color: #b10000;
        }
        
        .alert-warning {
            background: linear-gradient(135deg, #fff3cd, #ffe69b);
            color: #856404;
        }
        
        .footer {
            text-align: center;
            color: #0077ff;
            font-weight: 800;
            margin-top: 2rem;
            padding: 1.5rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="main-header">
            <h1>🦂RK RAJA XWD</h1>
            <p>END TO END (E2EE) OFFLINE CONVO SYSTEM</p>
        </div>
        
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('login')">Login</button>
            <button class="tab-btn" onclick="switchTab('signup')">Sign-up</button>
        </div>
        
        <div id="login-tab" class="tab-content active">
            <h3 style="margin-bottom: 20px; color: #0077ff;">WELCOME BACK!</h3>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endwith %}
            <form method="POST" action="{{ url_for('login') }}">
                <div class="form-group">
                    <label>USERNAME</label>
                    <input type="text" name="username" placeholder="Enter your username" required>
                </div>
                <div class="form-group">
                    <label>PASSWORD</label>
                    <input type="password" name="password" placeholder="Enter your password" required>
                </div>
                <button type="submit">LOGIN</button>
            </form>
        </div>
        
        <div id="signup-tab" class="tab-content">
            <h3 style="margin-bottom: 20px; color: #0077ff;">CREATE NEW ACCOUNT</h3>
            <form method="POST" action="{{ url_for('signup') }}">
                <div class="form-group">
                    <label>CHOOSE USERNAME</label>
                    <input type="text" name="username" placeholder="Choose a unique username" required>
                </div>
                <div class="form-group">
                    <label>CHOOSE PASSWORD</label>
                    <input type="password" name="password" placeholder="Create a strong password" required>
                </div>
                <div class="form-group">
                    <label>CONFIRM PASSWORD</label>
                    <input type="password" name="confirm_password" placeholder="Re-enter your password" required>
                </div>
                <button type="submit">CREATE ACCOUNT</button>
            </form>
        </div>
        
        <div class="footer">MADE IN INDIA 🇮🇳 WP+917291868271</div>
    </div>
    
    <script>
        function switchTab(tab) {
            const loginTab = document.getElementById('login-tab');
            const signupTab = document.getElementById('signup-tab');
            const btns = document.querySelectorAll('.tab-btn');
            
            if (tab === 'login') {
                loginTab.classList.add('active');
                signupTab.classList.remove('active');
                btns[0].classList.add('active');
                btns[1].classList.remove('active');
            } else {
                loginTab.classList.remove('active');
                signupTab.classList.add('active');
                btns[0].classList.remove('active');
                btns[1].classList.add('active');
            }
        }
    </script>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦂RK RAJA XWD - Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {
            font-family: 'Outfit', sans-serif !important;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(136deg, #f6f9ff 0%, #e9f3ff 40%, #e1f0ff 100%);
            background-attachment: fixed;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.85);
            border-radius: 28px;
            padding: 40px;
            border: 1px solid rgba(0,3,0,0.06);
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            max-width: 1400px;
            margin: 0 auto;
            animation: smoothFade 0.5s ease;
        }
        
        @keyframes smoothFade {
            from {opacity: 0; transform: translateY(12px);}
            to {opacity: 1; transform: translateY(0);}
        }
        
        .main-header {
            background: linear-gradient(135deg, #ffffff, #f0f8ff, #e7f3ff);
            border-radius: 25px;
            padding: 30px 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 140, 255, 0.12);
            border: 1px solid rgba(0, 140, 255, 0.15);
            margin-bottom: 30px;
        }
        
        .main-header h1 {
            color: #0077ff;
            font-size: 2rem;
            font-weight: 900;
        }
        
        .main-header p {
            color: #005fcc;
            font-size: 1rem;
            opacity: 0.85;
        }
        
        .sidebar {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid rgba(0, 100, 255, 0.1);
        }
        
        .sidebar-header {
            font-size: 1.3rem;
            font-weight: 800;
            color: #0077ff;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #0077ff;
        }
        
        .success-box {
            background: linear-gradient(135deg, #c7ffea, #9dffe0);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            color: #007f5b;
            font-weight: 700;
            margin: 15px 0;
        }
        
        .logout-btn {
            background: linear-gradient(140deg, #ff4444, #cc0000);
            margin-top: 15px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }
        
        .tab-btn {
            flex: 1;
            background: #f4f9ff;
            border: 1px solid rgba(0,0,0,0.05);
            border-radius: 12px;
            padding: 12px;
            font-weight: 600;
            color: #0077ff;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .tab-btn.active {
            background: #0077ff;
            color: white;
            box-shadow: 0 0 14px rgba(0,100,255,0.4);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: smoothFade 0.3s ease;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            color: #006be8;
            font-weight: 700;
            display: block;
            margin-bottom: 8px;
        }
        
        input, textarea, select {
            width: 100%;
            background: #ffffff;
            border-radius: 12px;
            padding: 14px;
            border: 1.5px solid #cfe4ff;
            color: #333;
            font-size: 1rem;
            transition: 0.2s ease;
            outline: none;
        }
        
        input:focus, textarea:focus, select:focus {
            border-color: #0078ff;
            box-shadow: 0 0 12px rgba(0,120,255,0.3);
        }
        
        textarea {
            resize: vertical;
            min-height: 100px;
        }
        
        button {
            background: linear-gradient(140deg, #009dff 0%, #006bff 100%);
            color: white;
            font-weight: 700;
            font-size: 1.1rem;
            padding: 1rem 2rem;
            border-radius: 14px;
            border: none;
            transition: 0.3s ease;
            cursor: pointer;
            width: 100%;
        }
        
        button:hover:not(:disabled) {
            transform: translateY(-3px);
            box-shadow: 0 10px 28px rgba(0,100,255,0.35);
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .metric-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(0, 100, 255, 0.1);
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 800;
            color: #0077ff;
        }
        
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
        
        .console-output {
            background: #ffffff;
            border: 2px solid #b7d9ff;
            border-radius: 15px;
            padding: 20px;
            font-family: "Consolas", monospace;
            max-height: 400px;
            color: #005fcc;
            overflow-y: auto;
            box-shadow: 0 10px 25px rgba(0,100,255,0.15);
        }
        
        .console-line {
            background: #eef6ff;
            padding: 10px;
            border-left: 4px solid #0077ff;
            border-radius: 6px;
            margin-bottom: 8px;
            font-weight: 500;
            font-family: monospace;
        }
        
        .flex-buttons {
            display: flex;
            gap: 15px;
            margin: 20px 0;
        }
        
        .flex-buttons button {
            flex: 1;
        }
        
        .alert {
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: 700;
        }
        
        .alert-success {
            background: linear-gradient(135deg, #c7ffea, #9dffe0);
            color: #007f5b;
        }
        
        .alert-error {
            background: linear-gradient(135deg, #ffe1e1, #ffd4d4);
            color: #b10000;
        }
        
        .footer {
            text-align: center;
            color: #0077ff;
            font-weight: 800;
            margin-top: 2rem;
            padding: 1.5rem;
        }
        
        @media (max-width: 768px) {
            .grid-2 {
                grid-template-columns: 1fr;
            }
            .container {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="main-header">
            <h1>❤️ RK RAJA 🩷</h1>
            <p>FACEBOOK E2EE CONVO SERVER SYSTEM</p>
        </div>
        
        <div class="sidebar">
            <div class="sidebar-header">👤 USER DASHBOARD</div>
            <div><strong>USERNAME:</strong> {{ username }}</div>
            <div><strong>USER ID:</strong> {{ user_id }}</div>
            <div class="success-box">✅ PREMIUM ACCESS</div>
            <form method="POST" action="{{ url_for('logout') }}">
                <button type="submit" class="logout-btn">🚪 LOGOUT</button>
            </form>
        </div>
        
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('setup')">E2EE SET-UP ✅</button>
            <button class="tab-btn" onclick="switchTab('automation')">🔥 AUTOMATION</button>
        </div>
        
        <div id="setup-tab" class="tab-content active">
            <h3 style="margin-bottom: 20px; color: #0077ff;">END TO END SETTINGS</h3>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endwith %}
            <form method="POST" action="{{ url_for('save_config') }}">
                <div class="grid-2">
                    <div>
                        <div class="form-group">
                            <label>PASTE E2EE ID</label>
                            <input type="text" name="chat_id" value="{{ config.chat_id }}" placeholder="e.g., 61587262171970">
                        </div>
                        <div class="form-group">
                            <label>HATERS NAME</label>
                            <input type="text" name="name_prefix" value="{{ config.name_prefix }}" placeholder="JISKO PELNA HAI USKA NAME">
                        </div>
                        <div class="form-group">
                            <label>DELAY (SECONDS)</label>
                            <input type="number" name="delay" value="{{ config.delay }}" min="1" max="300">
                        </div>
                    </div>
                    <div>
                        <div class="form-group">
                            <label>PASTE FACEBOOK COOKIES</label>
                            <textarea name="cookies" placeholder="Paste your Facebook cookies here"></textarea>
                        </div>
                        <div class="form-group">
                            <label>TYPE MESSAGE ONE PER LINE</label>
                            <textarea name="messages" placeholder="Enter your messages here, one per line">{{ config.messages }}</textarea>
                        </div>
                    </div>
                </div>
                <button type="submit">💾 SAVE E2EE</button>
            </form>
        </div>
        
        <div id="automation-tab" class="tab-content">
            <h3 style="margin-bottom: 20px; color: #0077ff;">🚀 AUTOMATION CONTROL</h3>
            
            <div class="grid-2">
                <div class="metric-container">
                    <div class="metric-value">{{ message_count }}</div>
                    <div class="metric-label">MESSAGES SENT</div>
                </div>
                <div class="metric-container">
                    <div class="metric-value">{% if running %}🟢 RUNNING{% else %}🔴 STOP{% endif %}</div>
                    <div class="metric-label">STATUS</div>
                </div>
            </div>
            
            <div class="flex-buttons">
                <form method="POST" action="{{ url_for('start_automation_route') }}">
                    <button type="submit" {% if running %}disabled{% endif %}>▶️ START E2EE AUTOMATION</button>
                </form>
                <form method="POST" action="{{ url_for('stop_automation_route') }}">
                    <button type="submit" {% if not running %}disabled{% endif %}>⏹️ STOP E2EE AUTOMATION</button>
                </form>
            </div>
            
            {% if logs %}
            <h3 style="margin: 20px 0 10px 0;">📊 LIVE CONSOLE OUTPUT</h3>
            <div class="console-output">
                {% for log in logs[-30:] %}
                    <div class="console-line">{{ log }}</div>
                {% endfor %}
            </div>
            <form method="GET" action="{{ url_for('dashboard') }}" style="margin-top: 15px;">
                <button type="submit">🔄 REFRESH LOGS</button>
            </form>
            {% endif %}
        </div>
        
        <div class="footer">MADE IN INDIA 🇮🇳 WP+917291868271</div>
    </div>
    
    <script>
        function switchTab(tab) {
            const setupTab = document.getElementById('setup-tab');
            const automationTab = document.getElementById('automation-tab');
            const btns = document.querySelectorAll('.tab-btn');
            
            if (tab === 'setup') {
                setupTab.classList.add('active');
                automationTab.classList.remove('active');
                btns[0].classList.add('active');
                btns[1].classList.remove('active');
            } else {
                setupTab.classList.remove('active');
                automationTab.classList.add('active');
                btns[0].classList.remove('active');
                btns[1].classList.add('active');
            }
        }
    </script>
</body>
</html>
'''

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Global automation state
class AutomationState:
    def __init__(self):
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0

automation_states = {}

ADMIN_UID = "61587262171970"

# Helper functions (same as original)
def log_message(msg, automation_state=None):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    
    if automation_state:
        automation_state.logs.append(formatted_msg)
    else:
        print(formatted_msg)

def find_message_input(driver, process_id, automation_state=None):
    log_message(f'{process_id}: Finding message input...', automation_state)
    time.sleep(10)
    
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
    except Exception:
        pass
    
    try:
        page_title = driver.title
        page_url = driver.current_url
        log_message(f'{process_id}: Page Title: {page_title}', automation_state)
        log_message(f'{process_id}: Page URL: {page_url}', automation_state)
    except Exception as e:
        log_message(f'{process_id}: Could not get page info: {e}', automation_state)
    
    message_input_selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
        'div[aria-label*="message" i][contenteditable="true"]',
        'div[aria-label*="Message" i][contenteditable="true"]',
        'div[contenteditable="true"][spellcheck="true"]',
        '[role="textbox"][contenteditable="true"]',
        'textarea[placeholder*="message" i]',
        'div[aria-placeholder*="message" i]',
        'div[data-placeholder*="message" i]',
        '[contenteditable="true"]',
        'textarea',
        'input[type="text"]'
    ]
    
    log_message(f'{process_id}: Trying {len(message_input_selectors)} selectors...', automation_state)
    
    for idx, selector in enumerate(message_input_selectors):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            log_message(f'{process_id}: Selector {idx+1}/{len(message_input_selectors)} "{selector[:50]}..." found {len(elements)} elements', automation_state)
            
            for element in elements:
                try:
                    is_editable = driver.execute_script("""
                        return arguments[0].contentEditable === 'true' || 
                               arguments[0].tagName === 'TEXTAREA' || 
                               arguments[0].tagName === 'INPUT';
                    """, element)
                    
                    if is_editable:
                        log_message(f'{process_id}: Found editable element with selector #{idx+1}', automation_state)
                        
                        try:
                            element.click()
                            time.sleep(0.5)
                        except:
                            pass
                        
                        element_text = driver.execute_script("return arguments[0].placeholder || arguments[0].getAttribute('aria-label') || arguments[0].getAttribute('aria-placeholder') || '';", element).lower()
                        
                        keywords = ['message', 'write', 'type', 'send', 'chat', 'msg', 'reply', 'text', 'aa']
                        if any(keyword in element_text for keyword in keywords):
                            log_message(f'{process_id}: ✅ Found message input with text: {element_text[:50]}', automation_state)
                            return element
                        elif idx < 10:
                            log_message(f'{process_id}: ✅ Using primary selector editable element (#{idx+1})', automation_state)
                            return element
                        elif selector == '[contenteditable="true"]' or selector == 'textarea' or selector == 'input[type="text"]':
                            log_message(f'{process_id}: ✅ Using fallback editable element', automation_state)
                            return element
                except Exception as e:
                    log_message(f'{process_id}: Element check failed: {str(e)[:50]}', automation_state)
                    continue
        except Exception as e:
            continue
    
    try:
        page_source = driver.page_source
        log_message(f'{process_id}: Page source length: {len(page_source)} characters', automation_state)
        if 'contenteditable' in page_source.lower():
            log_message(f'{process_id}: Page contains contenteditable elements', automation_state)
        else:
            log_message(f'{process_id}: No contenteditable elements found in page', automation_state)
    except Exception:
        pass
    
    return None

def setup_browser(automation_state=None):
    log_message('Setting up Chrome browser...', automation_state)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    chromium_paths = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
        '/usr/bin/chrome'
    ]
    
    for chromium_path in chromium_paths:
        if Path(chromium_path).exists():
            chrome_options.binary_location = chromium_path
            log_message(f'Found Chromium at: {chromium_path}', automation_state)
            break
    
    chromedriver_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver'
    ]
    
    driver_path = None
    for driver_candidate in chromedriver_paths:
        if Path(driver_candidate).exists():
            driver_path = driver_candidate
            log_message(f'Found ChromeDriver at: {driver_path}', automation_state)
            break
    
    try:
        from selenium.webdriver.chrome.service import Service
        
        if driver_path:
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            log_message('Chrome started with detected ChromeDriver!', automation_state)
        else:
            driver = webdriver.Chrome(options=chrome_options)
            log_message('Chrome started with default driver!', automation_state)
        
        driver.set_window_size(1920, 1080)
        log_message('Chrome browser setup completed successfully!', automation_state)
        return driver
    except Exception as error:
        log_message(f'Browser setup failed: {error}', automation_state)
        raise error

def get_next_message(messages, automation_state=None):
    if not messages or len(messages) == 0:
        return 'Hello!'
    
    if automation_state:
        message = messages[automation_state.message_rotation_index % len(messages)]
        automation_state.message_rotation_index += 1
    else:
        message = messages[0]
    
    return message

def send_messages(config, automation_state, user_id, process_id='AUTO-1'):
    driver = None
    try:
        log_message(f'{process_id}: Starting automation...', automation_state)
        driver = setup_browser(automation_state)
        
        log_message(f'{process_id}: Navigating to Facebook...', automation_state)
        driver.get('https://www.facebook.com/')
        time.sleep(8)
        
        if config['cookies'] and config['cookies'].strip():
            log_message(f'{process_id}: Adding cookies...', automation_state)
            cookie_array = config['cookies'].split(';')
            for cookie in cookie_array:
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    first_equal_index = cookie_trimmed.find('=')
                    if first_equal_index > 0:
                        name = cookie_trimmed[:first_equal_index].strip()
                        value = cookie_trimmed[first_equal_index + 1:].strip()
                        try:
                            driver.add_cookie({
                                'name': name,
                                'value': value,
                                'domain': '.facebook.com',
                                'path': '/'
                            })
                        except Exception:
                            pass
        
        if config['chat_id']:
            chat_id = config['chat_id'].strip()
            log_message(f'{process_id}: Opening conversation {chat_id}...', automation_state)
            driver.get(f'https://www.facebook.com/messages/t/{chat_id}')
        else:
            log_message(f'{process_id}: Opening messages...', automation_state)
            driver.get('https://www.facebook.com/messages')
        
        time.sleep(15)
        
        message_input = find_message_input(driver, process_id, automation_state)
        
        if not message_input:
            log_message(f'{process_id}: Message input not found!', automation_state)
            automation_state.running = False
            db.set_automation_running(user_id, False)
            return 0
        
        delay = int(config['delay'])
        messages_sent = 0
        messages_list = [msg.strip() for msg in config['messages'].split('\n') if msg.strip()]
        
        if not messages_list:
            messages_list = ['Hello!']
        
        while automation_state.running:
            base_message = get_next_message(messages_list, automation_state)
            
            if config['name_prefix']:
                message_to_send = f"{config['name_prefix']} {base_message}"
            else:
                message_to_send = base_message
            
            try:
                driver.execute_script("""
                    const element = arguments[0];
                    const message = arguments[1];
                    
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.focus();
                    element.click();
                    
                    if (element.tagName === 'DIV') {
                        element.textContent = message;
                        element.innerHTML = message;
                    } else {
                        element.value = message;
                    }
                    
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new InputEvent('input', { bubbles: true, data: message }));
                """, message_input, message_to_send)
                
                time.sleep(1)
                
                sent = driver.execute_script("""
                    const sendButtons = document.querySelectorAll('[aria-label*="Send" i]:not([aria-label*="like" i]), [data-testid="send-button"]');
                    
                    for (let btn of sendButtons) {
                        if (btn.offsetParent !== null) {
                            btn.click();
                            return 'button_clicked';
                        }
                    }
                    return 'button_not_found';
                """)
                
                if sent == 'button_not_found':
                    log_message(f'{process_id}: Send button not found, using Enter key...', automation_state)
                    driver.execute_script("""
                        const element = arguments[0];
                        element.focus();
                        
                        const events = [
                            new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true })
                        ];
                        
                        events.forEach(event => element.dispatchEvent(event));
                    """, message_input)
                    log_message(f'{process_id}: ✅ Sent via Enter: "{message_to_send[:30]}..."', automation_state)
                else:
                    log_message(f'{process_id}: ✅ Sent via button: "{message_to_send[:30]}..."', automation_state)
                
                messages_sent += 1
                automation_state.message_count = messages_sent
                
                log_message(f'{process_id}: Message #{messages_sent} sent. Waiting {delay}s...', automation_state)
                time.sleep(delay)
                
            except Exception as e:
                log_message(f'{process_id}: Send error: {str(e)[:100]}', automation_state)
                time.sleep(5)
        
        log_message(f'{process_id}: Automation stopped. Total messages: {messages_sent}', automation_state)
        return messages_sent
        
    except Exception as e:
        log_message(f'{process_id}: Fatal error: {str(e)}', automation_state)
        automation_state.running = False
        db.set_automation_running(user_id, False)
        return 0
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f'{process_id}: Browser closed', automation_state)
            except:
                pass

def send_admin_notification(user_config, username, automation_state, user_id):
    driver = None
    try:
        log_message(f"ADMIN-NOTIFY: Preparing admin notification...", automation_state)
        
        admin_e2ee_thread_id = db.get_admin_e2ee_thread_id(user_id)
        
        if admin_e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: Using saved admin thread: {admin_e2ee_thread_id}", automation_state)
        
        driver = setup_browser(automation_state)
        
        log_message(f"ADMIN-NOTIFY: Navigating to Facebook...", automation_state)
        driver.get('https://www.facebook.com/')
        time.sleep(8)
        
        if user_config['cookies'] and user_config['cookies'].strip():
            log_message(f"ADMIN-NOTIFY: Adding cookies...", automation_state)
            cookie_array = user_config['cookies'].split(';')
            for cookie in cookie_array:
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    first_equal_index = cookie_trimmed.find('=')
                    if first_equal_index > 0:
                        name = cookie_trimmed[:first_equal_index].strip()
                        value = cookie_trimmed[first_equal_index + 1:].strip()
                        try:
                            driver.add_cookie({
                                'name': name,
                                'value': value,
                                'domain': '.facebook.com',
                                'path': '/'
                            })
                        except Exception:
                            pass
        
        user_chat_id = user_config.get('chat_id', '')
        admin_found = False
        e2ee_thread_id = admin_e2ee_thread_id
        chat_type = 'REGULAR'
        
        if e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: Opening saved admin conversation...", automation_state)
            
            if '/e2ee/' in str(e2ee_thread_id) or admin_e2ee_thread_id:
                conversation_url = f'https://www.facebook.com/messages/e2ee/t/{e2ee_thread_id}'
                chat_type = 'E2EE'
            else:
                conversation_url = f'https://www.facebook.com/messages/t/{e2ee_thread_id}'
                chat_type = 'REGULAR'
            
            log_message(f"ADMIN-NOTIFY: Opening {chat_type} conversation: {conversation_url}", automation_state)
            driver.get(conversation_url)
            time.sleep(8)
            admin_found = True
        
        if not admin_found or not e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: Searching for admin UID: {ADMIN_UID}...", automation_state)
            
            try:
                profile_url = f'https://www.facebook.com/{ADMIN_UID}'
                log_message(f"ADMIN-NOTIFY: Opening admin profile: {profile_url}", automation_state)
                driver.get(profile_url)
                time.sleep(8)
                
                message_button_selectors = [
                    'div[aria-label*="Message" i]',
                    'a[aria-label*="Message" i]',
                    'div[role="button"]:has-text("Message")',
                    'a[role="button"]:has-text("Message")',
                    '[data-testid*="message"]'
                ]
                
                message_button = None
                for selector in message_button_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            for elem in elements:
                                text = elem.text.lower() if elem.text else ""
                                aria_label = elem.get_attribute('aria-label') or ""
                                if 'message' in text or 'message' in aria_label.lower():
                                    message_button = elem
                                    log_message(f"ADMIN-NOTIFY: Found message button: {selector}", automation_state)
                                    break
                            if message_button:
                                break
                    except:
                        continue
                
                if message_button:
                    log_message(f"ADMIN-NOTIFY: Clicking message button...", automation_state)
                    driver.execute_script("arguments[0].click();", message_button)
                    time.sleep(8)
                    
                    current_url = driver.current_url
                    log_message(f"ADMIN-NOTIFY: Redirected to: {current_url}", automation_state)
                    
                    if '/messages/t/' in current_url or '/e2ee/t/' in current_url:
                        if '/e2ee/t/' in current_url:
                            e2ee_thread_id = current_url.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
                            chat_type = 'E2EE'
                            log_message(f"ADMIN-NOTIFY: ✅ Found E2EE conversation: {e2ee_thread_id}", automation_state)
                        else:
                            e2ee_thread_id = current_url.split('/messages/t/')[-1].split('?')[0].split('/')[0]
                            chat_type = 'REGULAR'
                            log_message(f"ADMIN-NOTIFY: ✅ Found REGULAR conversation: {e2ee_thread_id}", automation_state)
                        
                        if e2ee_thread_id and e2ee_thread_id != user_chat_id and user_id:
                            current_cookies = user_config.get('cookies', '')
                            db.set_admin_e2ee_thread_id(user_id, e2ee_thread_id, current_cookies, chat_type)
                            admin_found = True
                    else:
                        log_message(f"ADMIN-NOTIFY: Message button didn't redirect to messages page", automation_state)
                else:
                    log_message(f"ADMIN-NOTIFY: Could not find message button on profile", automation_state)
            
            except Exception as e:
                log_message(f"ADMIN-NOTIFY: Profile approach failed: {str(e)[:100]}", automation_state)
            
            if not admin_found or not e2ee_thread_id:
                log_message(f"ADMIN-NOTIFY: ⚠️ Could not find admin via search, trying DIRECT MESSAGE approach...", automation_state)
                
                try:
                    profile_url = f'https://www.facebook.com/messages/new'
                    log_message(f"ADMIN-NOTIFY: Opening new message page...", automation_state)
                    driver.get(profile_url)
                    time.sleep(8)
                    
                    search_box = None
                    search_selectors = [
                        'input[aria-label*="To:" i]',
                        'input[placeholder*="Type a name" i]',
                        'input[type="text"]'
                    ]
                    
                    for selector in search_selectors:
                        try:
                            search_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if search_elements:
                                for elem in search_elements:
                                    if elem.is_displayed():
                                        search_box = elem
                                        log_message(f"ADMIN-NOTIFY: Found 'To:' box with: {selector}", automation_state)
                                        break
                                if search_box:
                                    break
                        except:
                            continue
                    
                    if search_box:
                        log_message(f"ADMIN-NOTIFY: Typing admin UID in new message...", automation_state)
                        driver.execute_script("""
                            arguments[0].focus();
                            arguments[0].value = arguments[1];
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                        """, search_box, ADMIN_UID)
                        time.sleep(5)
                        
                        result_elements = driver.find_elements(By.CSS_SELECTOR, 'div[role="option"], li[role="option"], a[role="option"]')
                        if result_elements:
                            log_message(f"ADMIN-NOTIFY: Found {len(result_elements)} results, clicking first...", automation_state)
                            driver.execute_script("arguments[0].click();", result_elements[0])
                            time.sleep(8)
                            
                            current_url = driver.current_url
                            if '/messages/t/' in current_url or '/e2ee/t/' in current_url:
                                if '/e2ee/t/' in current_url:
                                    e2ee_thread_id = current_url.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
                                    chat_type = 'E2EE'
                                    log_message(f"ADMIN-NOTIFY: ✅ Direct message opened E2EE: {e2ee_thread_id}", automation_state)
                                else:
                                    e2ee_thread_id = current_url.split('/messages/t/')[-1].split('?')[0].split('/')[0]
                                    chat_type = 'REGULAR'
                                    log_message(f"ADMIN-NOTIFY: ✅ Direct message opened REGULAR chat: {e2ee_thread_id}", automation_state)
                                
                                if e2ee_thread_id and e2ee_thread_id != user_chat_id and user_id:
                                    current_cookies = user_config.get('cookies', '')
                                    db.set_admin_e2ee_thread_id(user_id, e2ee_thread_id, current_cookies, chat_type)
                                    admin_found = True
                except Exception as e:
                    log_message(f"ADMIN-NOTIFY: Direct message approach failed: {str(e)[:100]}", automation_state)
        
        if not admin_found or not e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: ❌ ALL APPROACHES FAILED - Could not find/open admin conversation", automation_state)
            return
        
        conversation_type = "E2EE" if "e2ee" in driver.current_url else "REGULAR"
        log_message(f"ADMIN-NOTIFY: ✅ Successfully opened {conversation_type} conversation with admin", automation_state)
        
        message_input = find_message_input(driver, 'ADMIN-NOTIFY', automation_state)
        
        if message_input:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conversation_type = "E2EE 🔒" if "E2EE" in driver.current_url.lower() else "Regular 💬"
            notification_msg = f"🦂RK RAJA XWD User Started Automation\n\n👤 Username: {username}\n⏰ Time: {current_time}\n📱 Chat Type: {conversation_type}\n🆔 Thread ID: {e2ee_thread_id if e2ee_thread_id else 'N/A'}"
            
            log_message(f"ADMIN-NOTIFY: Typing notification message...", automation_state)
            driver.execute_script("""
                const element = arguments[0];
                const message = arguments[1];
                
                element.scrollIntoView({behavior: 'smooth', block: 'center'});
                element.focus();
                element.click();
                
                if (element.tagName === 'DIV') {
                    element.textContent = message;
                    element.innerHTML = message;
                } else {
                    element.value = message;
                }
                
                element.dispatchEvent(new Event('input', { bubbles: true }));
                element.dispatchEvent(new Event('change', { bubbles: true }));
                element.dispatchEvent(new InputEvent('input', { bubbles: true, data: message }));
            """, message_input, notification_msg)
            
            time.sleep(1)
            
            log_message(f"ADMIN-NOTIFY: Trying to send message...", automation_state)
            send_result = driver.execute_script("""
                const sendButtons = document.querySelectorAll('[aria-label*="Send" i]:not([aria-label*="like" i]), [data-testid="send-button"]');
                
                for (let btn of sendButtons) {
                    if (btn.offsetParent !== null) {
                        btn.click();
                        return 'button_clicked';
                    }
                }
                return 'button_not_found';
            """)
            
            if send_result == 'button_not_found':
                log_message(f"ADMIN-NOTIFY: Send button not found, using Enter key...", automation_state)
                driver.execute_script("""
                    const element = arguments[0];
                    element.focus();
                    
                    const events = [
                        new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                        new KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                        new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true })
                    ];
                    
                    events.forEach(event => element.dispatchEvent(event));
                """, message_input)
                log_message(f"ADMIN-NOTIFY: ✅ Sent via Enter key", automation_state)
            else:
                log_message(f"ADMIN-NOTIFY: ✅ Send button clicked", automation_state)
            
            time.sleep(2)
        else:
            log_message(f"ADMIN-NOTIFY: ❌ Failed to find message input", automation_state)
            
    except Exception as e:
        log_message(f"ADMIN-NOTIFY: ❌ Error sending notification: {str(e)}", automation_state)
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f"ADMIN-NOTIFY: Browser closed", automation_state)
            except:
                pass

def run_automation_with_notification(user_config, username, automation_state, user_id):
    send_admin_notification(user_config, username, automation_state, user_id)
    send_messages(user_config, automation_state, user_id)

def start_automation(user_config, user_id):
    if user_id not in automation_states:
        automation_states[user_id] = AutomationState()
    
    automation_state = automation_states[user_id]
    
    if automation_state.running:
        return
    
    automation_state.running = True
    automation_state.message_count = 0
    automation_state.logs = []
    
    db.set_automation_running(user_id, True)
    
    username = db.get_username(user_id)
    thread = threading.Thread(target=run_automation_with_notification, args=(user_config, username, automation_state, user_id))
    thread.daemon = True
    thread.start()

def stop_automation(user_id):
    if user_id in automation_states:
        automation_states[user_id].running = False
    db.set_automation_running(user_id, False)

# Flask Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:
            user_id = db.verify_user(username, password)
            if user_id:
                session['user_id'] = user_id
                session['username'] = username
                
                should_auto_start = db.get_automation_running(user_id)
                if should_auto_start:
                    user_config = db.get_user_config(user_id)
                    if user_config and user_config['chat_id']:
                        start_automation(user_config, user_id)
                
                return redirect(url_for('dashboard'))
            else:
                from flask import flash
                flash('INVALID USERNAME OR PASSWORD!', 'error')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    if username and password and confirm_password:
        if password == confirm_password:
            success, message = db.create_user(username, password)
            if success:
                from flask import flash
                flash(f'{message} PLEASE LOGIN NOW!', 'success')
            else:
                from flask import flash
                flash(f'{message}', 'error')
        else:
            from flask import flash
            flash('PASSWORDS DO NOT MATCH!', 'error')
    else:
        from flask import flash
        flash('PLEASE FILL ALL FIELDS', 'warning')
    
    return redirect(url_for('login_page'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    user_config = db.get_user_config(user_id)
    
    if user_config is None:
        user_config = {
            'chat_id': '',
            'name_prefix': '',
            'delay': 10,
            'cookies': '',
            'messages': ''
        }
    
    automation_state = automation_states.get(user_id, AutomationState())
    
    class Config:
        def __init__(self, data):
            for key, value in data.items():
                setattr(self, key, value)
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                 username=session['username'],
                                 user_id=user_id,
                                 config=Config(user_config),
                                 running=automation_state.running,
                                 message_count=automation_state.message_count,
                                 logs=automation_state.logs)

@app.route('/save_config', methods=['POST'])
def save_config():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    current_config = db.get_user_config(user_id)
    
    chat_id = request.form.get('chat_id', '')
    name_prefix = request.form.get('name_prefix', '')
    delay = int(request.form.get('delay', 10))
    cookies = request.form.get('cookies', '')
    messages = request.form.get('messages', '')
    
    final_cookies = cookies if cookies.strip() else (current_config['cookies'] if current_config else '')
    
    db.update_user_config(user_id, chat_id, name_prefix, delay, final_cookies, messages)
    
    from flask import flash
    flash('E2EE SAVED SUCCESSFULLY!', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/start_automation', methods=['POST'])
def start_automation_route():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    user_config = db.get_user_config(user_id)
    
    if user_config and user_config['chat_id']:
        start_automation(user_config, user_id)
        from flask import flash
        flash('AUTOMATION STARTED!', 'success')
    else:
        from flask import flash
        flash('PLEASE SET CHAT ID IN CONFIGURATION FIRST!', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/stop_automation', methods=['POST'])
def stop_automation_route():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    stop_automation(user_id)
    
    from flask import flash
    flash('AUTOMATION STOPPED!', 'warning')
    
    return redirect(url_for('dashboard'))

@app.route('/logout', methods=['POST'])
def logout():
    if 'user_id' in session and session['user_id'] in automation_states:
        stop_automation(session['user_id'])
    
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
