import requests
import getpass
import threading
import time
from utils import load_config, clean_arg

def fetch_messages(url, room, last_count):
    """Background thread to keep pulling new messages."""
    while True:
        try:
            response = requests.get(f"{url}/messages/{room}")
            if response.status_code == 200:
                msgs = response.json()
                if len(msgs) > last_count:
                    # Print only new messages
                    for i in range(last_count, len(msgs)):
                        print(f"\r[{msgs[i]['sender']}]: {msgs[i]['content']}")
                    last_count = len(msgs)
                    print("> ", end="", flush=True) # Keep the input prompt
        except:
            pass
        time.sleep(2)

def run(args):
    """Starts the chat interface."""
    if not args:
        print("Usage: xtc start:chat @room_name")
        return
    
    server_url = load_config()
    room_name = clean_arg(args[0])
    user = getpass.getuser()
    
    print(f"--- XTC-CLI: Room '{room_name}' (User: {user}) ---")
    print("Type your message and press Enter. Ctrl+C to exit.")

    # Start the message listener thread
    threading.Thread(target=fetch_messages, args=(server_url, room_name, 0), daemon=True).start()

    # Main thread handles sending messages
    try:
        while True:
            msg = input("> ")
            if msg.strip():
                requests.post(f"{server_url}/send", json={
                    "room": room_name, 
                    "user": user, 
                    "content": msg
                })
    except KeyboardInterrupt:
        print("\nExiting chat...")