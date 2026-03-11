import requests
from utils import load_config

def run(args):
    """Menampilkan daftar public room yang tidak memiliki password."""
    url = load_config()
    
    if not url:
        print("\033[31m[!] ERROR: No active server connection.\033[0m")
        return

    # Bersihkan URL dari trailing slash
    url = url.rstrip('/')

    print("\n\033[1m XTERMCHAT PUBLIC GATEWAY \033[0m")
    print("\033[2m" + "─"*45 + "\033[0m")

    try:
        # Request ke endpoint /rooms di Ubuntu
        res = requests.get(f"{url}/rooms", timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            rooms = data.get("rooms", [])
            
            if not rooms:
                print(" \033[33mNo public rooms available at the moment.\033[0m")
            else:
                # Header Tabel
                print(f" \033[2m{'ID':<4} {'ROOM NAME':<20} {'ACCESS':<10}\033[0m")
                print(" \033[2m" + "─"*40 + "\033[0m")
                
                for i, room in enumerate(rooms, 1):
                    room_name = room.get('name', 'unknown')
                    # Menggunakan warna hijau untuk kesan 'Open'
                    print(f" {i:<4} \033[1;32m@{room_name:<20}\033[0m \033[32mOPEN\033[0m")
            
            print(f"\n Total: {data.get('count', 0)} public access point(s)")
            
        else:
            print(f" \033[1;31m[!] SERVER_ERROR: {res.status_code}\033[0m")

    except Exception as e:
        print(f" \033[1;31m[!] CONNECTION_FAILED\033[0m")
        print(f" \033[2mError: {str(e)[:45]}...\033[0m")

    print("\033[2m" + "─"*45 + "\033[0m\n")