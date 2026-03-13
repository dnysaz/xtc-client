import time
import requests
import getpass
import subprocess
import socket
from utils import load_config, clean_arg

def get_hw_id():
    """Mengambil UUID Hardware Mac sebagai identitas unik."""
    try:
        # Command khusus macOS untuk mengambil Platform UUID
        cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep -E 'IOPlatformUUID' | awk '{print $3}' | tr -d '\"'"
        uuid = subprocess.check_output(cmd, shell=True).decode().strip()
        return uuid
    except:
        # Fallback ke hostname jika gagal (untuk keamanan tambahan)
        return socket.gethostname()

def run(args):
    """Creates a new room with Hardware ID (PIN) verification."""
    raw_url = load_config()
    if not raw_url:
        print("\033[31m[!] ERROR: No server connection.\033[0m")
        return
        
    server_url = raw_url.rstrip('/')
    
    # Logika Interaktif
    if len(args) < 1:
        try:
            print("\n" + "="*30)
            print("  \033[34mCREATE NEW ROOM\033[0m")
            print("="*30)
            
            room_name = input("> Room Name        : ").strip()
            if not room_name:
                print("\033[31m[!] Error: Room name cannot be empty.\033[0m")
                return
            
            password = input("> Room Password    : ").strip()
            description = input("> Room Description : ").strip()
            
            confirm = input("\n> Save to Gateway? (Yes/No): ").strip().lower()
            
            if confirm not in ['yes', 'y']:
                print("[*] Aborted.")
                return
                
            room_name = clean_arg(room_name)
        except KeyboardInterrupt:
            print("\n[*] Aborted.")
            return
    else:
        room_name = clean_arg(args[0])
        password = args[1] if len(args) > 1 else ""
        description = "Created via CLI arguments" 

    # Eksekusi ke Server
    try:
        # Persiapkan Identitas
        created_at_val = int(time.time())
        my_pin = get_hw_id()
        
        # Kirim Payload Lengkap
        response = requests.post(f"{server_url}/create-room", json={
            "room": room_name, 
            "password": password,
            "description": description,
            "user": getpass.getuser(),
            "created_at": created_at_val,
            "pin": my_pin  # Identitas unik Mac kamu
        }, timeout=10)
        
        data = response.json()
        if response.status_code == 201:
            print(f"\n\033[32m[*] SUCCESS: Room '@{room_name}' is live with Hardware ID Protection.\033[0m")
        else:
            print(f"\n\033[31m[!] FAILED: {data.get('message', 'Room already exists')}\033[0m")
            
    except Exception as e:
        print(f"\n\033[31m[!] CONNECTION ERROR: {e}\033[0m")