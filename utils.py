import json
import os
import socket
import subprocess

# Path absolut ke home directory agar bisa diakses dari folder mana pun
HOME_DIR    = os.path.expanduser("~")
CONFIG_FILE = os.path.join(HOME_DIR, ".xtc_config.json")


def get_hw_id():
    """
    Mengambil UUID hardware device sebagai identitas unik (Hardware PIN).
    - macOS : IOPlatformUUID via ioreg
    - Linux : machine-id via /etc/machine-id
    - Fallback : hostname
    Fungsi ini dipusatkan di utils.py agar semua command
    (create, delete, chat) pakai sumber yang sama.
    """
    # macOS
    try:
        cmd  = "ioreg -rd1 -c IOPlatformExpertDevice | grep -E 'IOPlatformUUID' | awk '{print $3}' | tr -d '\"'"
        uuid = subprocess.check_output(cmd, shell=True).decode().strip()
        if uuid:
            return uuid
    except Exception:
        pass

    # Linux
    try:
        with open("/etc/machine-id", "r") as f:
            machine_id = f.read().strip()
        if machine_id:
            return machine_id
    except Exception:
        pass

    # Fallback
    return socket.gethostname()


def load_config():
    """Baca server URL dari ~/.xtc_config.json."""
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("server_url")
    except (json.JSONDecodeError, IOError):
        return None


def save_config(url):
    """Simpan server URL ke ~/.xtc_config.json."""
    if not url:
        # URL kosong = disconnect, hapus file config
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        return

    # Tambahkan scheme dan port default jika belum ada
    if not url.startswith("http"):
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
    """Hapus karakter '@' dari argument command."""
    if not arg:
        return ""
    return arg.replace("@", "").strip()