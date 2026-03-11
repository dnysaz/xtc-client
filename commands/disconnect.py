from utils import save_config

def run(args):
    """Handles the disconnect command to clear the server URL."""
    if not args:
        print("\033[31m[!] Usage: xtc disconnect @<server_url>\033[0m")
        return
    
    # Target server yang ingin diputuskan
    target_ip = args[0].replace("@", "")
    
    # Menghapus config dengan menyimpan string kosong atau None
    # Tergantung bagaimana utils.save_config kamu bekerja
    try:
        save_config("") 
        print(f"\033[32m[*] SUCCESS: Disconnected from @{target_ip}.\033[0m")
        print("\033[2m[*] Configuration cleared.\033[0m")
    except Exception as e:
        print(f"\033[31m[!] ERROR: Failed to disconnect. {e}\033[0m")