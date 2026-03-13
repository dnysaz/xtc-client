import requests
from utils import load_config

def run(args):
    """Menampilkan daftar room dari gateway dengan status akses yang benar."""
    url = load_config()
    
    if not url:
        print("\033[31m[!] ERROR: No active server connection.\033[0m")
        return

    url = url.rstrip('/')

    print("\n\033[1m XTERMCHAT GATEWAY SERVICES \033[0m")
    print("\033[2m" + "─"*45 + "\033[0m")

    try:
        res = requests.get(f"{url}/rooms", timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            rooms = data.get("rooms", [])
            
            if not rooms:
                print(" \033[33mNo rooms available at the moment.\033[0m")
            else:
                # Header Tabel
                print(f" \033[2m{'ID':<4} {'ROOM NAME':<20} {'ACCESS':<10}\033[0m")
                print(" \033[2m" + "─"*40 + "\033[0m")
                
                for i, room in enumerate(rooms, 1):
                    room_name = room.get('name', 'unknown')
                    # Cek flag has_password dari server
                    is_secured = room.get('has_password', False)
                    
                    if is_secured:
                        access_status = "LOCKED"
                        color = "\033[1;33m" # Kuning Tebal
                        status_color = "\033[33m"
                    else:
                        access_status = "OPEN"
                        color = "\033[1;32m" # Hijau Tebal
                        status_color = "\033[32m"

                    print(f" {i:<4} {color}@{room_name:<20}\033[0m {status_color}{access_status}\033[0m")
            
            print(f"\n Total: {data.get('count', 0)} gateway access point(s)")
            
        else:
            print(f" \033[1;31m[!] SERVER_ERROR: {res.status_code}\033[0m")

    except Exception as e:
        print(f" \033[1;31m[!] CONNECTION_FAILED\033[0m")
        print(f" \033[2mError: {str(e)[:45]}...\033[0m")

    print("\033[2m" + "─"*45 + "\033[0m\n")