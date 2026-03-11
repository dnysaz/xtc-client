import requests
import getpass
from utils import load_config, clean_arg

def run(args):
    """Deletes a room only if the user is the original creator with confirmation."""
    if not args:
        print("Usage: xtc delete:room @room_name")
        return
    
    server_url = load_config()
    room_name = clean_arg(args[0])
    
    # Konfirmasi pengguna
    # Konfirmasi pengguna dengan new line setelah nama room
    confirm = input(
        f"Are you sure to delete this room '@{room_name}'?\n"
        "All chat and history will be deleted permanently and can't be restored. Yes/No ? "
    ).strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("[*] Deletion cancelled.")
        return
    
    try:
        response = requests.post(f"{server_url}/delete-room", json={
            "room": room_name, 
            "user": getpass.getuser()
        })
        
        data = response.json()
        if data.get("status") == "success":
            print(f"[*] Room '@{room_name}' deleted successfully.")
        else:
            print("[!] Failed to delete room. You are not the creator or the room does not exist.")
            
    except Exception as e:
        print(f"[!] Connection error: {e}")