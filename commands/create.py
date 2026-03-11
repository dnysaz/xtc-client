import requests
import getpass
from utils import load_config, clean_arg

def run(args):
    """Creates a new room. Password is optional."""
    # Ubah menjadi < 1 agar room_name tetap wajib, tapi password tidak
    if len(args) < 1:
        print("Usage: xtc create:room @room_name [password]")
        return
    
    server_url = load_config()
    room_name = clean_arg(args[0])
    
    # Ambil password dari argumen ke-2 jika ada, jika tidak, kosongkan
    password = args[1] if len(args) > 1 else ""
    
    try:
        response = requests.post(f"{server_url}/create-room", json={
            "room": room_name, 
            "password": password,
            "user": getpass.getuser()
        })
        
        data = response.json()
        # Cek status code 201 (Created) dari server kita
        if response.status_code == 201 and data.get("status") == "success":
            print(f"[*] Room '@{room_name}' created successfully.")
        else:
            print(f"[!] Failed: {data.get('message', 'Room might already exist')}")
            
    except Exception as e:
        print(f"[!] Connection error: {e}")