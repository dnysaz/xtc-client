import threading
import time
import requests
import getpass
import re
import shutil
import socket
from datetime import datetime, timezone

from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML, to_formatted_text
from prompt_toolkit.styles import Style
from prompt_toolkit.filters import HasFocus

from utils import load_config, clean_arg, save_config

url_regex = re.compile(r"(https?://[^\s]+)")

# Emoji Dictionary
EMOJI_MAP = {
    ":fire": "🔥",
    ":nice": "👍",
    ":cool": "😎",
    ":rocket": "🚀",
    ":laugh": "😂",
    ":warn": "⚠️",
    ":check": "✅",
    ":heart": "❤️",
    ":star": "⭐",
    ":ghost": "👻"
}

def get_human_time(ts):
    now = datetime.now(timezone.utc)
    diff = (now - ts).total_seconds()

    if diff < 60: 
        return "a sec.."
    if diff < 3600: 
        return f"{int(diff // 60)}m"
    if diff < 86400: 
        return f"{int(diff // 3600)}h"
    
    if ts.date() != now.date():
        return ts.strftime("%d %b")
        
    return ts.strftime("%H:%M")

def get_public_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=3).text
    except:
        return "ERR_CONN"

def run(args):
    raw_url = load_config()
    
    if not raw_url:
        print("\033[31m[!] ERROR: No active server connection.\033[0m")
        print("    Please run: \033[32mxtc connect @<server_ip>\033[0m")
        return

    url = raw_url.rstrip('/') 
    
    if not args:
        print("Usage: xtc start:chat @<room_name>")
        return

    room = clean_arg(args[0])
    password = args[1] if len(args) > 1 else "" 
    user = getpass.getuser()
    
    try:
        server_host = url.split("//")[-1].split(":")[0]
        server_ip = socket.gethostbyname(server_host)
    except:
        server_ip = "127.0.0.1"
    
    my_ip = get_public_ip()

    attempts = 0
    max_attempts = 3
    
    while True:
        try:
            res = requests.post(f"{url}/verify-room", json={"room": room, "password": password}, timeout=5)
            
            if res.status_code == 200:
                break
            
            elif res.status_code == 403:
                if password != "":
                    attempts += 1
                
                if attempts >= max_attempts:
                    print(f"\n\033[1;31m[!] SECURITY ALERT: {max_attempts} failed attempts.\033[0m")
                    print("\033[31m[!] Disconnecting from server for security reasons...\033[0m")
                    save_config("") 
                    return

                if attempts > 0:
                    print(f"\033[33m[!] Invalid password ({attempts}/{max_attempts})\033[0m")
                
                password = getpass.getpass("\033[31m[!] Password required: \033[0m")
                
                if not password:
                    print("[*] Access denied. Password cannot be empty.")
                    return
                continue
            
            elif res.status_code == 404:
                print(f"\033[31m[!] ERROR: Room '@{room}' not found.\033[0m")
                return

            else:
                print(f"[!] SERVER_ERROR: Received status {res.status_code} from {server_ip}")
                return

        except requests.exceptions.ConnectionError:
            print(f"\033[31m[!] OFFLINE: Cannot connect to {server_ip}.\033[0m")
            return
        except requests.exceptions.Timeout:
            print(f"\033[31m[!] TIMEOUT: Server at {server_ip} is taking too long to respond.\033[0m")
            return
        except Exception as e:
            print(f"[!] UNEXPECTED_ERROR: {e}")
            return

    chat_area = TextArea(read_only=True, scrollbar=True, wrap_lines=True, focusable=True, style="class:chat-content")
    input_area = TextArea(height=8, multiline=True, prompt=" Message >> ", style="class:input-text")

    def get_header_text():
        now = datetime.now().strftime('%H:%M:%S')
        return f" | XtermChat v1.0 | {server_ip} | {now} "

    def clock_scheduler(app):
        while True:
            time.sleep(1)
            app.invalidate()

    def fetch_messages(app):
        nonlocal password
        last_msgs = []
        while True:
            try:
                res = requests.get(f"{url}/messages/{room}", params={"password": password}, timeout=5)
                if res.status_code == 200:
                    msgs = res.json()
                    if msgs != last_msgs:
                        lines = [""]
                        for m in msgs:
                            db_time = m.get("created_at") or m.get("timestamp")
                            if db_time:
                                ts = datetime.fromisoformat(db_time.replace("Z", "+00:00"))
                            else:
                                ts = datetime.now(timezone.utc)
                            
                            t_str = get_human_time(ts)
                            content = url_regex.sub(r' <u>\g<0></u> ', m.get("content", ""))
                            
                            is_me = m['sender'] == user
                            s_style = "me" if is_me else "sender"
                            
                            line = f"<dim>[</dim> <time>{t_str:4}</time> <dim>]</dim> <{s_style}>{m['sender'][:10]:10}</{s_style}> <dim>❯</dim> {content}"
                            lines.append(line)
                        
                        for _ in range(4): lines.append("")

                        full_text = "".join([t for s, t in to_formatted_text(HTML("\n".join(lines)))])
                        new_cursor_pos = len(full_text) if len(msgs) > len(last_msgs) else chat_area.buffer.cursor_position
                        chat_area.buffer.set_document(Document(text=full_text, cursor_position=new_cursor_pos), bypass_readonly=True)
                        last_msgs = msgs
                        app.invalidate()
            except: pass
            time.sleep(2)

    kb = KeyBindings()
    @kb.add("c-c")
    def _(event): event.app.exit()
    @kb.add("enter", filter=HasFocus(input_area))
    def _(event):
        msg = input_area.text.strip()
        if not msg:
            return

        # Handle List Emoji Shortcut
        if msg == ":e":
            help_text = "\n <dim>❯ SYSTEM:</dim> <me>Available Emoji Shortcuts:</me>\n"
            for code, icon in EMOJI_MAP.items():
                help_text += f"   <dim>-</dim> {code:8} <sender>{icon}</sender>\n"
            
            current_text = chat_area.text
            new_text = current_text + "".join([t for s, t in to_formatted_text(HTML(help_text))])
            chat_area.buffer.set_document(Document(text=new_text, cursor_position=len(new_text)), bypass_readonly=True)
            input_area.text = ""
            return

        # Replace Emoji Shortcuts
        for code, icon in EMOJI_MAP.items():
            msg = msg.replace(code, icon)

        try:
            requests.post(f"{url}/send", json={"room": room, "password": password, "user": user, "content": msg}, timeout=5)
            input_area.text = ""
        except: pass

    style = Style.from_dict({
        '': '#00ff00 bg:#000000',
        'chat-content': 'bg:#080808',
        'u': '#00ffff underline bold', 
        'time': '#008800 bold',
        'sender': '#00ff00 bold',
        'me': '#00ffff bold', 
        'dim': '#004400',
        'header': 'bg:#00ff00 #000000 bold',
        'sidebar': 'bg:#000000 #00bb00',
        'sidebar.label': '#004400',
        'input-text': '#00ff00 bg:#000000',
        'status': 'bg:#002200 #00ff00 italic',
    })

    sidebar_content = HTML(
        f"\n<sidebar.label>  ROOM </sidebar.label>\n"
        f"  {room.upper()[:12]}\n\n"
        f"<sidebar.label>  USER </sidebar.label>\n"
        f"  {user[:12]}\n\n"
        f"<sidebar.label>  SRV_IP </sidebar.label>\n"
        f"  {server_ip}\n\n"
        f"<sidebar.label>  MY_IP </sidebar.label>\n"
        f"  {my_ip}\n\n"
        f"<sidebar.label>  STATUS </sidebar.label>\n"
        f"  ONLINE"
    )

    layout = Layout(HSplit([
        Window(height=1, style="class:header", content=FormattedTextControl(text=get_header_text)),
        VSplit([
            Window(width=20, content=FormattedTextControl(sidebar_content), style="class:sidebar"),
            Window(width=1, char="│", style="class:dim"),
            chat_area,
        ]),
        Window(height=1, style="class:status", content=FormattedTextControl(text=" [MOUSE SCROLL] HISTORY | [ENTER] SEND | [:e] EMOJIS | [CTRL+C] EXIT ")),
        input_area
    ]))

    app = Application(layout=layout, key_bindings=kb, full_screen=True, style=style, mouse_support=True)
    app.layout.focus(input_area)
    
    threading.Thread(target=fetch_messages, args=(app,), daemon=True).start()
    threading.Thread(target=clock_scheduler, args=(app,), daemon=True).start()
    app.run()