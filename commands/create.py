import requests
import getpass
from utils import load_config, clean_arg

def run(args):
    """Creates a new room and sets the current user as the owner."""
    if not args:
        print("Usage: xtc create:room @room_name")
        return
    
    server_url = load_config()
    room_name = clean_arg(args[0])
    
    try:
        response = requests.post(f"{server_url}/create-room", json={
            "room": room_name, 
            "user": getpass.getuser()
        })
        
        data = response.json()
        if data.get("status") == "success":
            print(f"[*] Room '@{room_name}' created successfully.")
        else:
            print("[!] Failed to create room (it might already exist).")
            
    except Exception as e:
        print(f"[!] Connection error: {e}")