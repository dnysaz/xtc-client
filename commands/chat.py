import threading
import time
import requests
import getpass
import re
import socket
import subprocess
from datetime import datetime, timezone

from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, Float, FloatContainer, ConditionalContainer
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML, to_formatted_text
from prompt_toolkit.styles import Style
from prompt_toolkit.filters import Condition, HasFocus

from utils import load_config, clean_arg, save_config

url_regex = re.compile(r"(https?://[^\s]+)")

EMOJI_MAP = {
    ":fire": "🔥", ":nice": "👍", ":cool": "😎", ":rocket": "🚀", ":laugh": "😂",
    ":warn": "⚠️", ":check": "✅", ":heart": "❤️", ":star": "⭐", ":ghost": "👻"
}

def get_hw_id():
    try:
        cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep -E 'IOPlatformUUID' | awk '{print $3}' | tr -d '\"'"
        uuid = subprocess.check_output(cmd, shell=True).decode().strip()
        return uuid
    except:
        return socket.gethostname()

CLI_PIN = get_hw_id()

def get_human_time(ts):
    now = datetime.now(timezone.utc)
    diff = (now - ts).total_seconds()
    if diff < 60: return "now"
    if diff < 3600: return f"{int(diff // 60)}m"
    return ts.strftime("%H:%M")

def get_public_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=3).text
    except:
        return "OFFLINE"

def run(args):
    raw_url = load_config()
    if not raw_url:
        print("\033[31m[!] ERROR: No server connection.\033[0m")
        return

    url = raw_url.rstrip('/') 
    if not args:
        print("Usage: xtc start:chat @room")
        return

    room = clean_arg(args[0])
    password = args[1] if len(args) > 1 else "" 
    user = getpass.getuser()[:5].upper()
    
    try:
        res = requests.post(f"{url}/verify-room", json={"room": room, "password": password}, timeout=5)
        if res.status_code == 404:
            print(f"\033[31m[!] ERROR: Room '@{room}' not found.\033[0m")
            return
        if res.status_code == 403:
            print(f"\n\033[33m> This room is private, please enter the Room password :\033[0m")
            password = getpass.getpass("  Password: ")
            res = requests.post(f"{url}/verify-room", json={"room": room, "password": password}, timeout=5)
            if res.status_code != 200:
                print(f"\033[31m[!] ACCESS DENIED: Invalid password.\033[0m")
                return
        if res.status_code != 200:
            print(f"\033[31m[!] SERVER ERROR: {res.status_code}\033[0m")
            return
    except Exception as e:
        print(f"\033[31m[!] CONNECTION FAILED: {e}\033[0m")
        return

    try:
        server_ip = socket.gethostbyname(url.split("//")[-1].split(":")[0])
    except:
        server_ip = "127.0.0.1"
    
    my_ip = get_public_ip()
    room_details = {"creator": "---", "description": "No description available."}

    try:
        r_info = requests.get(f"{url}/rooms", timeout=3).json()
        for r in r_info.get('rooms', []):
            if r['name'] == room:
                room_details['creator'] = r.get('creator', 'SYSTEM')[:10].upper()
                room_details['description'] = r.get('description', 'No description.')
    except: pass

    # UI Components
    chat_area = TextArea(read_only=True, scrollbar=True, wrap_lines=True, style="class:chat-content")
    input_area = TextArea(height=4, multiline=True, prompt=" Message ❯❯❯ ", style="class:input-text")
    right_sidebar_area = TextArea(read_only=True, focusable=False, wrap_lines=True, style="class:sidebar")

    show_emoji_modal = [False]

    emoji_list_text = "\n".join([f" <me>{k:8}</me> <white>{v}</white>" for k, v in EMOJI_MAP.items()])
    emoji_modal_content = TextArea(
        text="".join([t for s, t in to_formatted_text(HTML(f"<b>EMOJI SHORTCUTS</b>\n\n{emoji_list_text}"))]),
        read_only=True, width=30, height=14, style="class:modal"
    )
    emoji_modal = Frame(emoji_modal_content, style="class:modal-border")

    def get_header_text():
        now = datetime.now().strftime('%H:%M:%S')
        return f"  XtermChat-CLI  |  NODE: {socket.gethostname()}  |  {server_ip}  "

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
                            db_time = m.get("timestamp")
                            try: ts = datetime.strptime(db_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                            except: ts = datetime.now(timezone.utc)
                            t_str = get_human_time(ts)
                            processed_content = url_regex.sub(r'<u>\g<0></u>', m.get("content", ""))
                            is_me = (m['sender'].lower() == user.lower() or str(m.get('pin')) == str(CLI_PIN))
                            if is_me:
                                line = f" <time>{t_str:4}</time> <me>YOU</me> <dim>❯</dim> <me_text>{processed_content}</me_text>"
                            else:
                                line = f" <time>{t_str:4}</time> <sender>{m['sender'][:5]:5}</sender> <dim>❯</dim> {processed_content}"
                            lines.append(line)
                        
                        # --- UPDATE: MENAMBAHKAN JARAK 5 BARIS DI AKHIR ---
                        lines.extend([""] * 5) 
                        full_text = "".join([t for s, t in to_formatted_text(HTML("\n".join(lines)))])
                        
                        # Set document dan kunci posisi ke pesan terakhir (sebelum padding baris kosong)
                        chat_area.buffer.set_document(Document(text=full_text, cursor_position=len(full_text)), bypass_readonly=True)
                        last_msgs = msgs
                        app.invalidate()
            except: pass
            time.sleep(2)

    kb = KeyBindings()
    @kb.add("c-c")
    def _(event): event.app.exit()

    @kb.add("escape")
    def _(event):
        show_emoji_modal[0] = False
        event.app.invalidate()

    # Navigasi Scroll Manual via Keyboard
    @kb.add("pageup")
    def _(event):
        chat_area.control.scroll_to_position((chat_area.control.vertical_scroll - 5, 0))

    @kb.add("pagedown")
    def _(event):
        chat_area.control.scroll_to_position((chat_area.control.vertical_scroll + 5, 0))

    @kb.add("enter", filter=HasFocus(input_area))
    def _(event):
        msg = input_area.text.strip()
        if not msg: return
        if msg == ":e":
            show_emoji_modal[0] = not show_emoji_modal[0]
            input_area.text = ""
            event.app.invalidate()
            return
        for code, icon in EMOJI_MAP.items(): msg = msg.replace(code, icon)
        try:
            payload = {"room": room, "password": password, "user": user, "content": msg, "pin": CLI_PIN}
            requests.post(f"{url}/send", json=payload, timeout=5)
            input_area.text = ""
        except: pass

    style = Style.from_dict({
        '': '#ffffff bg:#000000',
        'chat-content': 'bg:#050505',
        'header': 'bg:#0084ff #ffffff bold',
        'sidebar': 'bg:#0a0a0a #666666',
        'sidebar.label': '#444444 bold',
        'sidebar.val': '#0084ff bold',
        'time': '#333333',
        'sender': '#ffffff bold',
        'me': '#0084ff bold',
        'me_text': '#00aaff',
        'dim': '#222222',
        'input-text': 'bg:#000000 #ffffff',
        'status': 'bg:#000000 #333333 italic',
        'modal': 'bg:#111111 #ffffff',
        'modal-border': '#0084ff bold',
    })

    left_side = HTML(
        f"\n <sidebar.label>ID</sidebar.label>\n"
        f" <sidebar.val> {user}</sidebar.val>\n\n"
        f" <sidebar.label>GATEWAY</sidebar.label>\n"
        f"  {server_ip}\n\n"
        f" <sidebar.label>PUB_IP</sidebar.label>\n"
        f"  {my_ip}\n\n"
        f" <sidebar.label>AUTH</sidebar.label>\n"
        f" <me> LOCKED</me>"
    )

    right_side_html = f"\n <sidebar.label>CHANNEL</sidebar.label>\n <sidebar.val> #{room[:10].upper()}</sidebar.val>\n\n <sidebar.label>CREATOR</sidebar.label>\n  {room_details['creator']}\n\n <sidebar.label>ABOUT</sidebar.label>\n <white>{room_details['description']}</white>"
    right_sidebar_area.buffer.set_document(Document(text="".join([t for s, t in to_formatted_text(HTML(right_side_html))])), bypass_readonly=True)

    body = VSplit([
        Window(width=20, content=FormattedTextControl(left_side), style="class:sidebar"),
        Window(width=1, char="│", style="class:dim"),
        chat_area,
        Window(width=1, char="│", style="class:dim"),
        Window(width=28, content=right_sidebar_area.control, style="class:sidebar"),
    ])

    root_container = FloatContainer(
        content=HSplit([
            Window(height=1, style="class:header", content=FormattedTextControl(text=get_header_text)),
            body,
            Window(height=1, style="class:status", content=FormattedTextControl(text=" [PGUP/PGDN] SCROLL | [ESC] CLOSE | [ENTER] SEND ")),
            input_area
        ]),
        floats=[
            Float(content=ConditionalContainer(
                content=emoji_modal,
                filter=Condition(lambda: show_emoji_modal[0])
            ))
        ]
    )

    app = Application(layout=Layout(root_container), key_bindings=kb, full_screen=True, style=style, mouse_support=True)
    app.layout.focus(input_area)
    threading.Thread(target=fetch_messages, args=(app,), daemon=True).start()
    app.run()