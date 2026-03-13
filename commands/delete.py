import requests
import getpass
from utils import load_config, clean_arg

def run(args):
    """Deletes a room permanently with strict validation."""
    if not args:
        print("Usage: xtc delete:room @room_name")
        return
    
    raw_url = load_config()
    if not raw_url:
        print("\033[31m[!] ERROR: No active server connection.\033[0m")
        return

    # Pastikan URL bersih dari double slash
    server_url = raw_url.rstrip('/')
    room_name = clean_arg(args[0])
    
    # Konfirmasi pengguna dengan gaya serius
    print(f"\n\033[33mARE YOU SURE TO DELETE ROOM '@{room_name}'?\033[0m")
    confirm = input(
        "All chat and history will be deleted permanently and can't be restored.\n"
        "Confirm Deletion? (Yes/No): "
    ).strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("[*] Deletion cancelled.")
        return
    
    try:
        # Kirim request ke server
        response = requests.post(f"{server_url}/delete-room", json={
            "room": room_name, 
            "user": getpass.getuser()
        }, timeout=10) # Tambahkan timeout agar tidak hang
        
        # Proteksi jika server mengirim error HTML bukan JSON
        if response.status_code != 200:
            print(f"\033[31m[!] SERVER_ERROR: Received status {response.status_code}\033[0m")
            return

        data = response.json()
        if data.get("status") == "success":
            print(f"\033[32m[*] SUCCESS: Room '@{room_name}' and its history have been wiped.\033[0m")
        else:
            error_msg = data.get("message", "You are not the creator or the room does not exist.")
            print(f"\033[31m[!] FAILED: {error_msg}\033[0m")
            
    except requests.exceptions.JSONDecodeError:
        print("\033[31m[!] ERROR: Server returned an invalid response. Check server logs.\033[0m")
    except Exception as e:
        print(f"\033[31m[!] CONNECTION ERROR: {e}\033[0m")