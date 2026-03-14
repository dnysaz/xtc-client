import time
import requests
import getpass
from utils import load_config, clean_arg, get_hw_id

# Karakter yang tidak boleh ada di nama room
INVALID_CHARS = set(' /\\@#?&=+%"\'<>{}|^`')

def validate_room_name(name):
    """Validasi nama room: tidak boleh kosong, mengandung karakter terlarang, atau terlalu panjang."""
    if not name:
        return False, "Room name cannot be empty."
    if len(name) > 32:
        return False, "Room name too long (max 32 characters)."
    if any(c in INVALID_CHARS for c in name):
        return False, f"Room name contains invalid characters. Use letters, numbers, hyphens, or underscores only."
    return True, ""


def run(args):
    """Creates a new room with Hardware ID (PIN) verification."""
    raw_url = load_config()
    if not raw_url:
        print("\033[31m[!] ERROR: No server connection. Run 'xtc connect @<ip>' first.\033[0m")
        return

    server_url = raw_url.rstrip('/')

    # ── Mode Interaktif (tanpa args) ──────────────────────────────────────────
    if len(args) < 1:
        try:
            print("\n" + "═"*34)
            print("  \033[1;34mCREATE NEW ROOM\033[0m")
            print("═"*34)

            room_name = input("> Room Name        : ").strip()
            valid, err = validate_room_name(room_name)
            if not valid:
                print(f"\033[31m[!] {err}\033[0m")
                return

            password    = input("> Room Password    : ").strip()
            description = input("> Room Description : ").strip()

            # Preview sebelum konfirmasi
            access = "PRIVATE 🔒" if password else "PUBLIC 🌐"
            print(f"\n  Name   : @{room_name}")
            print(f"  Access : {access}")
            print(f"  About  : {description or '—'}")

            confirm = input("\n> Save to Gateway? (Yes/No): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("[*] Aborted.")
                return

            room_name = clean_arg(room_name)

        except KeyboardInterrupt:
            print("\n[*] Aborted.")
            return

    # ── Mode Quick (dengan args) ──────────────────────────────────────────────
    else:
        room_name   = clean_arg(args[0])
        password    = args[1] if len(args) > 1 else ""
        description = args[2] if len(args) > 2 else ""

        valid, err = validate_room_name(room_name)
        if not valid:
            print(f"\033[31m[!] {err}\033[0m")
            return

    # ── Kirim ke Server ───────────────────────────────────────────────────────
    try:
        my_pin = get_hw_id()   # ← dari utils.py, bukan definisi lokal

        response = requests.post(f"{server_url}/create-room", json={
            "room":        room_name,
            "password":    password,
            "description": description,
            "user":        getpass.getuser(),
            "created_at":  int(time.time()),
            "pin":         my_pin
        }, timeout=10)

        data = response.json()

        if response.status_code == 201:
            access = "private 🔒" if password else "public 🌐"
            print(f"\n\033[32m[*] SUCCESS: Room '@{room_name}' is live ({access}) with Hardware ID Protection.\033[0m")
        elif response.status_code == 400:
            print(f"\n\033[31m[!] FAILED: {data.get('message', 'Room already exists.')}\033[0m")
        elif response.status_code == 500:
            print(f"\n\033[31m[!] SERVER ERROR: {data.get('message', 'Internal server error.')}\033[0m")
        else:
            print(f"\n\033[31m[!] UNEXPECTED: Status {response.status_code} — {data.get('message', '')}\033[0m")

    except requests.exceptions.ConnectionError:
        print(f"\n\033[31m[!] CONNECTION ERROR: Cannot reach server. Run 'xtc status' to check.\033[0m")
    except requests.exceptions.Timeout:
        print(f"\n\033[31m[!] TIMEOUT: Server did not respond within 10 seconds.\033[0m")
    except Exception as e:
        print(f"\n\033[31m[!] ERROR: {e}\033[0m")