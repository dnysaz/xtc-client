import json
import os
import sys

CONFIG_FILE = "config.json"

def load_config():
    """Reads the server URL configuration from config.json."""
    if not os.path.exists(CONFIG_FILE):
        print("[!] Error: Configuration not found. Run 'xtc connect @ip_server' first.")
        sys.exit(1)
    
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        return config.get("server_url")

def save_config(url):
    """Saves the server URL to config.json."""
    # Ensure the URL starts with http/https
    if not url.startswith("http"):
        url = f"http://{url}"
        
    with open(CONFIG_FILE, "w") as f:
        json.dump({"server_url": url}, f)
    print(f"[*] Connected to server: {url}")

def clean_arg(arg):
    """Removes the '@' character from the command argument."""
    return arg.replace("@", "")