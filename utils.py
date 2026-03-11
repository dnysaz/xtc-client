import json
import os
import sys

# Menggunakan path absolut ke home directory agar bisa diakses dari folder mana pun
HOME_DIR = os.path.expanduser("~")
CONFIG_FILE = os.path.join(HOME_DIR, ".xtc_config.json")

def load_config():
    """Reads the server URL configuration from ~/.xtc_config.json."""
    if not os.path.exists(CONFIG_FILE):
        # Kita return None saja, biarkan command 'status' atau 'chat' yang handle pesan errornya
        return None
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("server_url")
    except (json.JSONDecodeError, IOError):
        return None

def save_config(url):
    """Saves the server URL to ~/.xtc_config.json."""
    if not url:
        # Jika URL kosong (saat disconnect), hapus filenya
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        return

    # Pastikan URL memiliki skema http dan port default jika hanya IP
    if not url.startswith("http"):
        # Jika tidak ada port (tidak ada titik dua setelah IP), tambahkan :8080
        if ":" not in url:
            url = f"http://{url}:8080"
        else:
            url = f"http://{url}"
        
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"server_url": url}, f, indent=4)
        print(f"\033[32m[*] Configuration saved to: {CONFIG_FILE}\033[0m")
        print(f"\033[32m[*] Linked to gateway: {url}\033[0m")
    except IOError as e:
        print(f"\033[31m[!] Failed to save configuration: {e}\033[0m")

def clean_arg(arg):
    """Removes the '@' character from the command argument."""
    if not arg:
        return ""
    return arg.replace("@", "")