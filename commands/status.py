import requests
import time
from utils import load_config

def run(args):
    """Mengecek status koneksi dengan teks standar dan warna pada status saja."""
    url = load_config()
    
    # Header menggunakan warna default terminal (hitam/putih)
    print("\n\033[1m XTERMCHAT CONNECTION STATUS \033[0m")
    print("\033[2m" + "─"*45 + "\033[0m")

    if not url:
        # Status Offline karena tidak ada config
        print(" STATUS  : \033[1;31mOFFLINE / NO CONFIG\033[0m")
        print(" ACTION  : Run 'xtc connect @<ip_server>'")
        print("\033[2m" + "─"*45 + "\033[0m\n")
        return

    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        latency = int((time.time() - start_time) * 1000)
        
        # Ambil data JSON dari server
        server_info = response.json() 
        status_code = response.status_code
        
        # Mapping data dari JSON server
        service = server_info.get("service", "Unknown")
        version = server_info.get("version", "0.0")
        srv_status = server_info.get("status", "online").upper()

        print(f" GATEWAY :  {url}")
        print(f" SERVICE :  {service} v{version}")
        
        # Hanya baris STATUS yang berwarna (Hijau jika Online)
        print(f" STATUS  :  \033[1;32m{srv_status} (HTTP {status_code})\033[0m")
        print(f" LATENCY :  {latency} ms")
        
    except Exception:
        # Status Offline (Merah jika Unreachable)
        print(f" GATEWAY :  {url}")
        print(f" STATUS  :  \033[1;31mOFFLINE / UNREACHABLE\033[0m")
        print(f" SERVER  :  Please check your server status.")

    print("\033[2m" + "─"*45 + "\033[0m\n")