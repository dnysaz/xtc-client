import requests
import time
from datetime import datetime
from utils import load_config

def format_date(timestamp):
    """Mengubah unix timestamp menjadi format tanggal terbaca."""
    if not timestamp or timestamp == 0:
        return "N/A"
    try:
        # Mengubah ke format: 13 Mar 2026
        return datetime.fromtimestamp(timestamp).strftime('%d %b %Y')
    except:
        return "Invalid"

def run(args):
    """Menampilkan daftar room dalam format tabel lengkap."""
    raw_url = load_config()
    
    if not raw_url:
        print("\033[31m[!] ERROR: No active server connection.\033[0m")
        return

    url = raw_url.rstrip('/')

    print("\n \033[1;34mXTERMCHAT GATEWAY SERVICES\033[0m")
    print(" \033[2m" + "━"*95 + "\033[0m")

    try:
        res = requests.get(f"{url}/rooms", timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            rooms = data.get("rooms", [])
            
            if not rooms:
                print(" \033[33mNo rooms available at the moment.\033[0m")
            else:
                # Header Tabel - Menyesuaikan kolom baru
                # ID(4) | NAME(18) | ACCESS(8) | CREATOR(12) | CREATED(15) | DESC
                header = f" \033[1m{'ID':<4} {'NAME':<18} {'ACCESS':<8} {'BY':<12} {'CREATED':<15} {'DESCRIPTION'}\033[0m"
                print(header)
                print(" \033[2m" + "─"*95 + "\033[0m")
                
                for i, room in enumerate(rooms, 1):
                    room_name = room.get('name', 'unknown')
                    is_secured = room.get('has_password', False)
                    creator = room.get('creator', 'SYSTEM')[:10]
                    # Ambil data created_at dari server
                    created_at = format_date(room.get('created_at', 0))
                    desc = room.get('description', '')[:30] # Potong jika kepanjangan

                    # Warna & Status Akses
                    if is_secured:
                        access_status = "LOCKED"
                        name_color = "\033[1;33m" # Kuning (Private)
                        acc_color = "\033[33m"
                    else:
                        access_status = "OPEN"
                        name_color = "\033[1;32m" # Hijau (Public)
                        acc_color = "\033[32m"

                    # Baris Data
                    row = (
                        f" {i:<4} "
                        f"{name_color}@{room_name:<17}\033[0m "
                        f"{acc_color}{access_status:<8}\033[0m "
                        f"\033[36m{creator:<12}\033[0m "
                        f"\033[2m{created_at:<15}\033[0m "
                        f"{desc}"
                    )
                    print(row)
            
            print(" \033[2m" + "─"*95 + "\033[0m")
            print(f" Total: {data.get('count', 0)} gateway access point(s)")
            
        else:
            print(f" \033[1;31m[!] SERVER_ERROR: {res.status_code}\033[0m")

    except Exception as e:
        print(f" \033[1;31m[!] CONNECTION_FAILED\033[0m")
        print(f" \033[2mError: {str(e)}\033[0m")

    print(" \033[2m" + "━"*95 + "\033[0m\n")