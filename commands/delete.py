import requests
import getpass
from utils import load_config, clean_arg, get_hw_id

def run(args):
    """Deletes a room permanently. Validates username + hardware PIN."""
    if not args:
        print("Usage: xtc delete:room @room_name")
        return

    raw_url = load_config()
    if not raw_url:
        print("\033[31m[!] ERROR: No active server connection.\033[0m")
        return

    server_url = raw_url.rstrip('/')
    room_name  = clean_arg(args[0])

    # Konfirmasi sebelum eksekusi
    print(f"\n\033[33mARE YOU SURE TO DELETE ROOM '@{room_name}'?\033[0m")
    confirm = input(
        "All chat and history will be deleted permanently and can't be restored.\n"
        "Confirm Deletion? (Yes/No): "
    ).strip().lower()

    if confirm not in ['yes', 'y']:
        print("[*] Deletion cancelled.")
        return

    try:
        response = requests.post(f"{server_url}/delete-room", json={
            "room": room_name,
            "user": getpass.getuser(),
            "pin":  get_hw_id()    # ← dari utils.py
        }, timeout=10)

        data = response.json()

        if response.status_code == 200 and data.get("status") == "success":
            print(f"\033[32m[*] SUCCESS: Room '@{room_name}' and its history have been wiped.\033[0m")
        else:
            error_msg = data.get("message", "You are not the creator or the room does not exist.")
            print(f"\033[31m[!] FAILED: {error_msg}\033[0m")

    except requests.exceptions.ConnectionError:
        print("\033[31m[!] CONNECTION ERROR: Cannot reach server. Run 'xtc status' to check.\033[0m")
    except requests.exceptions.Timeout:
        print("\033[31m[!] TIMEOUT: Server did not respond within 10 seconds.\033[0m")
    except requests.exceptions.JSONDecodeError:
        print("\033[31m[!] ERROR: Server returned an invalid response. Check server logs.\033[0m")
    except Exception as e:
        print(f"\033[31m[!] CONNECTION ERROR: {e}\033[0m")