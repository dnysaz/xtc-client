import requests
import getpass
from utils import load_config, clean_arg

def run(args):
    """Creates a new room with interactive prompts if no args provided."""
    server_url = load_config()
    
    # Logika Interaktif jika tidak ada argumen
    if len(args) < 1:
        try:
            print("\n" + "="*30)
            print("  CREATE NEW CHANNEL  ")
            print("="*30)
            
            room_name = input("> room name : ").strip()
            if not room_name:
                print("[!] Error: Room name cannot be empty.")
                return
            
            # Menggunakan getpass agar input password tidak terlihat (opsional)
            # Atau input biasa jika ingin terlihat apa yang diketik
            password = input("> room password (leave blank for public): ").strip()
            description = input("> room description : ").strip()
            
            confirm = input("> save? (Yes/No): ").strip().lower()
            
            if confirm not in ['yes', 'y']:
                print("[*] Aborted.")
                return
                
            room_name = clean_arg(room_name)
        except KeyboardInterrupt:
            print("\n[*] Aborted.")
            return
    else:
        # Tetap mendukung mode cepat via argumen: xtc create:room @name pass
        room_name = clean_arg(args[0])
        password = args[1] if len(args) > 1 else ""
        description = "" # Default kosong jika lewat argumen cepat

    # Eksekusi ke Server
    try:
        # Kirim data ke gateway Ubuntu
        response = requests.post(f"{server_url}/create-room", json={
            "room": room_name, 
            "password": password,
            "description": description, # Pastikan server.py kamu juga menangani field ini
            "user": getpass.getuser()
        })
        
        data = response.json()
        if response.status_code == 201 and data.get("status") == "success":
            print(f"\n[*] Success: Room '@{room_name}' is now live.")
        else:
            print(f"\n[!] Failed: {data.get('message', 'Room might already exist')}")
            
    except Exception as e:
        print(f"\n[!] Connection error: {e}")