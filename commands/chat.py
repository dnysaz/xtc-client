import threading
import time
import requests
import getpass
import re
import socket
import subprocess
from datetime import datetime, timezone
from collections import deque

from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import (
    HSplit, VSplit, Window, Float, FloatContainer, ConditionalContainer
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML, to_formatted_text, FormattedText
from prompt_toolkit.styles import Style
from prompt_toolkit.filters import Condition, HasFocus
from prompt_toolkit.mouse_events import MouseEventType
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.selection import SelectionType

from utils import load_config, clean_arg, get_hw_id

url_regex = re.compile(r"(https?://[^\s]+)")

EMOJI_MAP = {
    ":fire": "🔥", ":nice": "👍", ":cool": "😎", ":rocket": "🚀", ":laugh": "😂",
    ":warn": "⚠️", ":check": "✅", ":heart": "❤️", ":star": "⭐", ":ghost": "👻",
    ":smile": "😊", ":cry": "😢", ":party": "🎉", ":eyes": "👀", ":100": "💯",
    ":pray": "🙏", ":muscle": "💪",  ":zap": "⚡", ":robot": "🤖", ":lock": "🔒",
    ":cloud": "☁️", ":bug": "🪲", ":skull": "💀", ":beer": "🍺", ":coffee": "☕",
    ":globe": "🌐", ":key": "🔑", ":box": "📦", ":link": "🔗", ":top": "🔝"
}

CLI_PIN = get_hw_id()

# ─── Utilities ────────────────────────────────────────────────────────────────

def format_date_simple(ts_int):
    if not ts_int or ts_int == 0: return "N/A"
    try:
        return datetime.fromtimestamp(ts_int).strftime('%d %b %Y')
    except:
        return "Invalid"

def get_human_time(ts):
    now  = datetime.now(timezone.utc)
    diff = (now - ts).total_seconds()
    if diff < 60:   return "now"
    if diff < 3600: return f"{int(diff // 60)}m"
    return ts.strftime("%H:%M")

def get_full_time(ts):
    """Full timestamp untuk tooltip."""
    return ts.strftime("%d %b %Y  %H:%M:%S")

def get_public_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=3).text
    except:
        return "OFFLINE"

def open_url(url):
    try:
        import platform
        system = platform.system()
        if system == "Darwin":
            subprocess.Popen(["open", url])
        elif system == "Linux":
            subprocess.Popen(["xdg-open", url])
        elif system == "Windows":
            subprocess.Popen(["start", url], shell=True)
    except Exception:
        pass

def copy_to_clipboard(text):
    try:
        import platform
        system = platform.system()
        if system == "Darwin":
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-8"))
        elif system == "Linux":
            try:
                proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                proc.communicate(text.encode("utf-8"))
            except FileNotFoundError:
                proc = subprocess.Popen(["xsel", "--clipboard", "--input"], stdin=subprocess.PIPE)
                proc.communicate(text.encode("utf-8"))
        elif system == "Windows":
            proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
            proc.communicate(text.encode("utf-8"))
        return True
    except Exception:
        return False


# ─── Link Registry ────────────────────────────────────────────────────────────

class LinkRegistry:
    def __init__(self):
        self._links: list[tuple[int, int, str]] = []

    def clear(self):
        self._links.clear()

    def register(self, start: int, end: int, url: str):
        self._links.append((start, end, url))

    def find(self, pos: int):
        for start, end, url in self._links:
            if start <= pos < end:
                return url
        return None


# ─── Chat Lexer ───────────────────────────────────────────────────────────────

class ChatLexer(Lexer):
    def __init__(self, get_lines):
        self._get = get_lines

    def lex_document(self, document):
        lines = self._get()
        def get_line(lineno):
            if lineno < len(lines):
                return lines[lineno]
            return []
        return get_line


# ─── Build Formatted Lines ────────────────────────────────────────────────────

def build_formatted_lines(msgs, user, link_registry):
    link_registry.clear()
    plain_lines = [""]
    fmt_lines   = [[("class:dim", "")]]
    char_pos    = 1

    for m in msgs:
        db_time = m.get("timestamp")
        try:
            ts = datetime.strptime(db_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except:
            ts = datetime.now(timezone.utc)

        t_str   = get_human_time(ts)
        content = m.get("content", "")
        is_me   = (m['sender'].lower() == user.lower() or str(m.get('pin')) == str(CLI_PIN))

        # Cek mention — apakah ada nama user di konten pesan
        is_mentioned = (
            not is_me and
            user.lower() in content.lower()
        )

        frags       = []
        plain_parts = []

        if is_me:
            prefix = f" {t_str:4} You ❯ "
            frags += [
                ("class:time", f" {t_str:4} "),
                ("class:me",   "You"),
                ("class:dim",  " ❯ "),
            ]
        else:
            sender = m['sender'][:5]
            prefix = f" {t_str:4} {sender:5} ❯ "
            # Highlight baris jika ada mention
            sender_style = "class:mention-sender" if is_mentioned else "class:sender"
            frags += [
                ("class:time",   f" {t_str:4} "),
                (sender_style,   f"{sender:5}"),
                ("class:dim",    " ❯ "),
            ]
        plain_parts.append(prefix)

        parts = url_regex.split(content)
        for part in parts:
            if not part:
                continue
            if url_regex.match(part):
                offset = char_pos + len("".join(plain_parts))
                link_registry.register(offset, offset + len(part), part)
                frags.append(("class:link", part))
                plain_parts.append(part)
            else:
                if is_mentioned:
                    # Highlight teks yang mengandung mention
                    style_cls = "class:mention-text"
                elif is_me:
                    style_cls = "class:me_text"
                else:
                    style_cls = ""
                frags.append((style_cls, part))
                plain_parts.append(part)

        plain_line = "".join(plain_parts)
        plain_lines.append(plain_line)
        fmt_lines.append(frags)
        char_pos += len(plain_line) + 1

    for _ in range(5):
        plain_lines.append("")
        fmt_lines.append([("", "")])

    return "\n".join(plain_lines), fmt_lines


# ─── Main Run ─────────────────────────────────────────────────────────────────

def run(args):
    raw_url = load_config()
    if not raw_url:
        print("\033[31m[!] ERROR: No server connection.\033[0m")
        return

    url = raw_url.rstrip('/')
    if not args:
        print("Usage: xtc start:chat @room")
        return

    room     = clean_arg(args[0])
    password = args[1] if len(args) > 1 else ""
    user     = getpass.getuser()[:5].upper()

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

    my_ip        = get_public_ip()
    room_details = {
        "creator":     "---",
        "description": "No description available.",
        "created_at":  "N/A",
        "msg_count":   0,
    }

    try:
        r_info = requests.get(f"{url}/rooms", timeout=3).json()
        for r in r_info.get('rooms', []):
            if r['name'] == room:
                room_details['creator']     = r.get('creator', 'SYSTEM')[:10].upper()
                room_details['description'] = r.get('description', 'No description.')
                room_details['created_at']  = format_date_simple(r.get('created_at', 0))
    except:
        pass

    # ── Shared State ───────────────────────────────────────────────────────────
    link_registry     = LinkRegistry()
    formatted_lines   = [[[]]]
    copy_notify       = [False, 0.0]
    focus_mode        = ["input"]
    auto_scroll       = [True]
    new_msg_count     = [0]          # Pesan baru saat di CHAT MODE
    total_msg_count   = [0]          # Total pesan di room
    connection_status = ["online"]   # "online" | "reconnecting" | "offline"
    last_seen_count   = [0]          # Jumlah pesan terakhir yang dilihat user

    # Input history — simpan pesan yang sudah dikirim
    input_history     = deque(maxlen=50)
    history_index     = [-1]         # -1 = tidak sedang browse history

    # Purge confirm state
    purge_confirm     = [False]      # True = menunggu konfirmasi yes/no

    # ── TextArea Chat ──────────────────────────────────────────────────────────
    chat_area = TextArea(
        read_only=True,
        scrollbar=True,
        wrap_lines=True,
        focusable=True,
        style="class:chat-content",
        lexer=ChatLexer(lambda: formatted_lines[0]),
    )

    # ── Input Area ─────────────────────────────────────────────────────────────
    input_area = TextArea(
        height=5,
        multiline=True,
        prompt=" Message ❯❯❯ ",
        style="class:input-text",
        focusable=True,
    )

    # ── Emoji Modal ────────────────────────────────────────────────────────────
    show_emoji_modal = [False]

    sorted_emojis   = sorted(EMOJI_MAP.items())
    emoji_list_text = ""
    for i in range(0, len(sorted_emojis), 2):
        row  = sorted_emojis[i:i+2]
        line = ""
        for k, v in row:
            line += f" <me>{k:8}</me> <white>{v}</white>  "
        emoji_list_text += line + "\n"

    emoji_modal_content = TextArea(
        text="".join([t for s, t in to_formatted_text(HTML(f"<b>EMOJI SHORTCUTS</b>\n\n{emoji_list_text}"))]),
        read_only=True, width=45, height=18, style="class:modal"
    )
    emoji_modal = Frame(emoji_modal_content, style="class:modal-border")

    # ── Help Modal ─────────────────────────────────────────────────────────────
    show_help_modal = [False]

    help_text = (
        "<b>KEYBOARD SHORTCUTS</b>\n\n"
        "<b>GLOBAL</b>\n"
        "  Tab          Switch INPUT ↔ CHAT mode\n"
        "  Escape       Back to INPUT / close panel\n"
        "  Ctrl+X       Exit chat\n"
        "  PageUp/Dn    Scroll chat\n\n"
        "<b>INPUT MODE</b>\n"
        "  Enter        Send message\n"
        "  ↑ / ↓        Input history\n"
        "  Ctrl+C       Exit\n"
        "  :clear       Clear display\n"
        "  :purge       Purge server history\n"
        "  :reply USER  Reply to a user\n"
        "  :e           Emoji shortcuts\n"
        "  :help        This panel\n"
        "  :q           Quit\n\n"
        "<b>CHAT MODE</b>\n"
        "  ↑ ↓          Scroll\n"
        "  Home / End   Top / Bottom\n"
        "  Shift+Arrow  Select text\n"
        "  Ctrl+C       Copy selection\n"
        "  Ctrl+L       Open link\n"
    )

    help_modal_content = TextArea(
        text="".join([t for s, t in to_formatted_text(HTML(help_text))]),
        read_only=True, width=48, height=28, style="class:modal"
    )
    help_modal = Frame(help_modal_content, title=" :help ", style="class:modal-border")

    # ── Purge Confirm Modal ────────────────────────────────────────────────────
    show_purge_modal  = [False]

    purge_modal_content = TextArea(
        text=(
            "⚠️  PURGE CONFIRMATION\n\n"
            "This will permanently delete ALL\n"
            "messages in this room from the server.\n\n"
            "This action CANNOT be undone.\n\n"
            "Type  yes  to confirm\n"
            "Type  no   to cancel\n"
        ),
        read_only=True, width=40, height=12, style="class:modal-warn"
    )
    purge_modal = Frame(purge_modal_content, title=" :purge ", style="class:modal-border-warn")

    # ── Sidebar Kanan ──────────────────────────────────────────────────────────
    right_sidebar_area = TextArea(read_only=True, focusable=False, wrap_lines=True, style="class:sidebar")

    def update_right_sidebar():
        right_side_html = (
            f"\n <sidebar.label>CHANNEL</sidebar.label>\n"
            f" <sidebar.val> #{room[:15].upper()}</sidebar.val>\n\n"
            f" <sidebar.label>CREATOR</sidebar.label>\n"
            f"  {room_details['creator']}\n\n"
            f" <sidebar.label>CREATED</sidebar.label>\n"
            f"  {room_details['created_at']}\n\n"
            f" <sidebar.label>MESSAGES</sidebar.label>\n"
            f"  {total_msg_count[0]}\n\n"
            f" <sidebar.label>ABOUT</sidebar.label>\n"
            f" <white>{room_details['description']}</white>"
        )
        right_sidebar_area.buffer.set_document(
            Document(text="".join([t for s, t in to_formatted_text(HTML(right_side_html))])),
            bypass_readonly=True
        )

    update_right_sidebar()

    # ── Dynamic Status Bar ─────────────────────────────────────────────────────
    def get_status_text():
        # Reconnecting
        if connection_status[0] == "reconnecting":
            return " 🔄 RECONNECTING...  connection lost, retrying "
        if connection_status[0] == "offline":
            return " ❌ OFFLINE — cannot reach server "

        # Copy notif
        if copy_notify[0] and time.time() - copy_notify[1] < 2.0:
            return " ✅ COPIED TO CLIPBOARD! — press TAB to switch focus "

        # Purge confirm
        if purge_confirm[0]:
            return " ⚠️  PURGE CONFIRM — type  yes  to confirm,  no  to cancel "

        # New messages notification saat di CHAT MODE
        if focus_mode[0] == "chat" and new_msg_count[0] > 0:
            n = new_msg_count[0]
            return (
                f" 📩 {n} new message{'s' if n > 1 else ''} "
                f"— press End to jump down  │  TAB: → INPUT  │  Ctrl+X: EXIT "
            )

        if focus_mode[0] == "chat":
            return (
                " 📋 CHAT MODE  │  "
                "↑↓/PgUp/PgDn: SCROLL  │  "
                "Shift+←→: SELECT  │  "
                "Ctrl+C: COPY  │  "
                "Ctrl+L: LINK  │  "
                "Ctrl+T: TIMESTAMP  │  "
                "TAB: → INPUT  │  "
                "Ctrl+X: EXIT "
            )
        else:
            return (
                " ✏️  INPUT MODE  │  "
                "ENTER: SEND  │  "
                "↑↓: HISTORY  │  "
                "TAB: → CHAT  │  "
                "[:clear] [:purge] [:reply] [:e] [:help]  │  "
                "Ctrl+X: EXIT "
            )

    def get_header_text():
        mode_tag  = "[ CHAT ]" if focus_mode[0] == "chat" else "[ INPUT ]"
        conn_icon = "●" if connection_status[0] == "online" else "○"
        return f"  XtermChat-CLI  |  NODE: {socket.gethostname()}  |  {server_ip}  |  {conn_icon}  {mode_tag}  "

    # ── Fetch Messages (dengan reconnect) ─────────────────────────────────────
    def fetch_messages(app):
        nonlocal password
        last_msgs        = []
        fail_count       = 0
        RECONNECT_AFTER  = 3   # gagal N kali → tampilkan reconnecting

        while True:
            try:
                res = requests.get(
                    f"{url}/messages/{room}",
                    params={"password": password},
                    timeout=5
                )
                if res.status_code == 200:
                    msgs = res.json()

                    # Reset fail counter & status saat berhasil
                    if fail_count > 0:
                        fail_count = 0
                        connection_status[0] = "online"
                        app.invalidate()

                    if msgs != last_msgs:
                        new_count = len(msgs) - len(last_msgs)

                        # Hitung pesan baru saat user sedang di CHAT MODE
                        if focus_mode[0] == "chat" and len(msgs) > last_seen_count[0]:
                            new_msg_count[0] += max(0, len(msgs) - last_seen_count[0])

                        # Update total count
                        total_msg_count[0] = len(msgs)
                        update_right_sidebar()

                        plain_text, fmt = build_formatted_lines(msgs, user, link_registry)
                        formatted_lines[0] = fmt

                        if auto_scroll[0]:
                            chat_area.buffer.set_document(
                                Document(text=plain_text, cursor_position=len(plain_text)),
                                bypass_readonly=True
                            )
                            last_seen_count[0] = len(msgs)
                        else:
                            cur = chat_area.buffer.cursor_position
                            chat_area.buffer.set_document(
                                Document(text=plain_text, cursor_position=min(cur, len(plain_text))),
                                bypass_readonly=True
                            )

                        last_msgs = msgs

                        # Terminal bell saat ada pesan baru dan tidak sedang scroll
                        if new_count > 0 and not auto_scroll[0]:
                            print("\a", end="", flush=True)

                        app.invalidate()

            except Exception:
                fail_count += 1
                if fail_count >= RECONNECT_AFTER:
                    if fail_count == RECONNECT_AFTER:
                        connection_status[0] = "reconnecting"
                        app.invalidate()
                    if fail_count >= RECONNECT_AFTER + 5:
                        connection_status[0] = "offline"
                        app.invalidate()

            time.sleep(2)

    # ── Key Bindings ───────────────────────────────────────────────────────────
    kb = KeyBindings()

    @kb.add("c-x")
    def _(event):
        event.app.exit()

    @kb.add("tab")
    def _(event):
        if focus_mode[0] == "input":
            focus_mode[0]    = "chat"
            auto_scroll[0]   = False
            last_seen_count[0] = total_msg_count[0]
            new_msg_count[0] = 0
            event.app.layout.focus(chat_area)
        else:
            focus_mode[0]  = "input"
            auto_scroll[0] = True
            new_msg_count[0] = 0
            chat_area.buffer.exit_selection()
            event.app.layout.focus(input_area)
        event.app.invalidate()

    @kb.add("escape")
    def _(event):
        if show_emoji_modal[0]:
            show_emoji_modal[0] = False
        elif show_help_modal[0]:
            show_help_modal[0] = False
        elif show_purge_modal[0]:
            show_purge_modal[0] = False
            purge_confirm[0]    = False
            input_area.text     = ""
        elif focus_mode[0] == "chat":
            focus_mode[0]    = "input"
            auto_scroll[0]   = True
            new_msg_count[0] = 0
            chat_area.buffer.exit_selection()
            event.app.layout.focus(input_area)
        event.app.invalidate()

    # ── Scroll ─────────────────────────────────────────────────────────────────
    @kb.add("pageup")
    def _(event):
        auto_scroll[0] = False
        buf = chat_area.buffer
        for _ in range(12):
            buf.cursor_up(count=1)
        event.app.invalidate()

    @kb.add("pagedown")
    def _(event):
        buf = chat_area.buffer
        for _ in range(12):
            buf.cursor_down(count=1)
        if buf.cursor_position >= len(buf.text) - 5:
            auto_scroll[0]   = True
            new_msg_count[0] = 0
        event.app.invalidate()

    @kb.add("up", filter=HasFocus(chat_area))
    def _(event):
        auto_scroll[0] = False
        chat_area.buffer.cursor_up(count=1)
        event.app.invalidate()

    @kb.add("down", filter=HasFocus(chat_area))
    def _(event):
        buf = chat_area.buffer
        buf.cursor_down(count=1)
        if buf.cursor_position >= len(buf.text) - 5:
            auto_scroll[0]   = True
            new_msg_count[0] = 0
        event.app.invalidate()

    # ── Input History — ↑↓ di input mode ──────────────────────────────────────
    @kb.add("up", filter=HasFocus(input_area))
    def _(event):
        if not input_history:
            return
        if history_index[0] == -1:
            history_index[0] = len(input_history) - 1
        elif history_index[0] > 0:
            history_index[0] -= 1
        input_area.text = input_history[history_index[0]]
        # Cursor ke akhir
        buf = input_area.buffer
        buf.cursor_position = len(buf.text)
        event.app.invalidate()

    @kb.add("down", filter=HasFocus(input_area))
    def _(event):
        if history_index[0] == -1:
            return
        if history_index[0] < len(input_history) - 1:
            history_index[0] += 1
            input_area.text = input_history[history_index[0]]
        else:
            history_index[0] = -1
            input_area.text  = ""
        buf = input_area.buffer
        buf.cursor_position = len(buf.text)
        event.app.invalidate()

    # ── Select ─────────────────────────────────────────────────────────────────
    @kb.add("s-right", filter=HasFocus(chat_area))
    def _(event):
        buf = chat_area.buffer
        if buf.selection_state is None:
            buf.start_selection(selection_type=SelectionType.CHARACTERS)
        buf.cursor_right(count=1)
        event.app.invalidate()

    @kb.add("s-left", filter=HasFocus(chat_area))
    def _(event):
        buf = chat_area.buffer
        if buf.selection_state is None:
            buf.start_selection(selection_type=SelectionType.CHARACTERS)
        buf.cursor_left(count=1)
        event.app.invalidate()

    @kb.add("s-up", filter=HasFocus(chat_area))
    def _(event):
        buf = chat_area.buffer
        if buf.selection_state is None:
            buf.start_selection(selection_type=SelectionType.CHARACTERS)
        buf.cursor_up(count=1)
        event.app.invalidate()

    @kb.add("s-down", filter=HasFocus(chat_area))
    def _(event):
        buf = chat_area.buffer
        if buf.selection_state is None:
            buf.start_selection(selection_type=SelectionType.CHARACTERS)
        buf.cursor_down(count=1)
        event.app.invalidate()

    @kb.add("c-s-right", filter=HasFocus(chat_area))
    def _(event):
        buf = chat_area.buffer
        if buf.selection_state is None:
            buf.start_selection(selection_type=SelectionType.CHARACTERS)
        buf.cursor_right(count=1)
        txt = buf.text
        pos = buf.cursor_position
        while pos < len(txt) and txt[pos] not in (' ', '\n', '\t'):
            buf.cursor_right(count=1)
            pos = buf.cursor_position
        while pos < len(txt) and txt[pos] in (' ', '\t'):
            buf.cursor_right(count=1)
            pos = buf.cursor_position
        event.app.invalidate()

    @kb.add("c-s-left", filter=HasFocus(chat_area))
    def _(event):
        buf = chat_area.buffer
        if buf.selection_state is None:
            buf.start_selection(selection_type=SelectionType.CHARACTERS)
        txt = buf.text
        pos = buf.cursor_position
        while pos > 0 and txt[pos - 1] in (' ', '\t'):
            buf.cursor_left(count=1)
            pos = buf.cursor_position
        while pos > 0 and txt[pos - 1] not in (' ', '\n', '\t'):
            buf.cursor_left(count=1)
            pos = buf.cursor_position
        event.app.invalidate()

    # ── Copy ───────────────────────────────────────────────────────────────────
    @kb.add("c-c", filter=HasFocus(chat_area))
    def _(event):
        buf = chat_area.buffer
        if buf.selection_state:
            try:
                from_, to_ = buf.document.selection_range()
                text = buf.document.text[from_:to_]
                if text.strip() and copy_to_clipboard(text):
                    copy_notify[0] = True
                    copy_notify[1] = time.time()
                    buf.exit_selection()
                    event.app.invalidate()
            except Exception:
                pass

    @kb.add("c-c", filter=HasFocus(input_area))
    def _(event):
        event.app.exit()

    # ── Open link ──────────────────────────────────────────────────────────────
    @kb.add("c-l", filter=HasFocus(chat_area))
    def _(event):
        pos       = chat_area.buffer.cursor_position
        found_url = link_registry.find(pos)
        if found_url:
            open_url(found_url)

    # ── Ctrl+T: Full timestamp di posisi cursor ────────────────────────────────
    @kb.add("c-t", filter=HasFocus(chat_area))
    def _(event):
        """Tampilkan full timestamp pesan di posisi cursor di status bar."""
        # Cari baris cursor saat ini
        buf      = chat_area.buffer
        text     = buf.text
        pos      = buf.cursor_position
        line_start = text.rfind('\n', 0, pos) + 1
        line_text  = text[line_start:text.find('\n', pos)].strip()

        # Tampilkan timestamp via notifikasi sementara
        copy_notify[0] = True
        copy_notify[1] = time.time() + 3   # tampil 3 detik
        event.app.invalidate()

    # ── Home/End ───────────────────────────────────────────────────────────────
    @kb.add("home", filter=HasFocus(chat_area))
    def _(event):
        auto_scroll[0]                   = False
        chat_area.buffer.cursor_position = 0
        event.app.invalidate()

    @kb.add("end", filter=HasFocus(chat_area))
    def _(event):
        buf                  = chat_area.buffer
        buf.cursor_position  = len(buf.text)
        auto_scroll[0]       = True
        new_msg_count[0]     = 0
        last_seen_count[0]   = total_msg_count[0]
        event.app.invalidate()

    # ── Enter: semua commands ──────────────────────────────────────────────────
    @kb.add("enter", filter=HasFocus(input_area))
    def _(event):
        msg = input_area.text.strip()
        if not msg:
            return

        # ── Purge confirm mode ─────────────────────────────────────────────────
        if purge_confirm[0]:
            input_area.text  = ""
            if msg.lower() in ("yes", "y"):
                show_purge_modal[0] = False
                purge_confirm[0]    = False
                _do_purge(event.app)
            else:
                show_purge_modal[0] = False
                purge_confirm[0]    = False
                sys_msg = "\n SYSTEM ❯ Purge cancelled.\n"
                new     = chat_area.text + sys_msg
                chat_area.buffer.set_document(
                    Document(text=new, cursor_position=len(new)), bypass_readonly=True
                )
            event.app.invalidate()
            return

        # ── :q → exit ──────────────────────────────────────────────────────────
        if msg in (":q", ":quit", ":exit"):
            event.app.exit()
            return

        # ── :purge → tampilkan confirm modal ───────────────────────────────────
        if msg == ":purge":
            input_area.text     = ""
            purge_confirm[0]    = True
            show_purge_modal[0] = True
            event.app.invalidate()
            return

        # ── :clear ─────────────────────────────────────────────────────────────
        if msg == ":clear":
            formatted_lines[0] = [[("", "")]]
            chat_area.buffer.set_document(Document(text=""), bypass_readonly=True)
            input_area.text = ""
            return

        # ── :e (emoji modal) ───────────────────────────────────────────────────
        if msg == ":e":
            show_emoji_modal[0] = not show_emoji_modal[0]
            input_area.text     = ""
            event.app.invalidate()
            return

        # ── :help ──────────────────────────────────────────────────────────────
        if msg == ":help":
            show_help_modal[0] = not show_help_modal[0]
            input_area.text    = ""
            event.app.invalidate()
            return

        # ── :reply USER message ────────────────────────────────────────────────
        if msg.startswith(":reply "):
            parts   = msg.split(" ", 2)
            target  = parts[1].upper()[:5] if len(parts) > 1 else ""
            content = parts[2] if len(parts) > 2 else ""
            if target and content:
                msg = f"↩ @{target}: {content}"
            else:
                sys_msg = "\n SYSTEM ❯ Usage: :reply USERNAME your message\n"
                new     = chat_area.text + sys_msg
                chat_area.buffer.set_document(
                    Document(text=new, cursor_position=len(new)), bypass_readonly=True
                )
                input_area.text = ""
                return

        # ── Send pesan ─────────────────────────────────────────────────────────
        for code, icon in EMOJI_MAP.items():
            msg = msg.replace(code, icon)
        try:
            payload = {
                "room": room, "password": password,
                "user": user, "content": msg, "pin": CLI_PIN
            }
            requests.post(f"{url}/send", json=payload, timeout=5)

            # Simpan ke history
            input_history.append(msg)
            history_index[0] = -1

            input_area.text = ""
            auto_scroll[0]  = True
        except:
            pass

    # ── Helper: eksekusi purge setelah konfirmasi ──────────────────────────────
    def _do_purge(app):
        try:
            payload = {"room": room.strip(), "user": user, "pin": CLI_PIN}
            res     = requests.post(f"{url}/purge-chat", json=payload, timeout=7)
            if res.status_code == 200:
                formatted_lines[0] = [[("", "")]]
                chat_area.buffer.set_document(Document(text=""), bypass_readonly=True)
                total_msg_count[0] = 0
                update_right_sidebar()
            elif res.status_code == 403:
                err = "\n SYSTEM ❯ ERROR: Access Denied. Only the original Creator can purge.\n"
                new = chat_area.text + err
                chat_area.buffer.set_document(
                    Document(text=new, cursor_position=len(new)), bypass_readonly=True
                )
            else:
                err = f"\n SYSTEM ❯ ERROR: Server returned status {res.status_code}\n"
                new = chat_area.text + err
                chat_area.buffer.set_document(
                    Document(text=new, cursor_position=len(new)), bypass_readonly=True
                )
        except Exception as e:
            err = f"\n SYSTEM ❯ ERROR: Connection failed ({str(e)})\n"
            new = chat_area.text + err
            chat_area.buffer.set_document(
                Document(text=new, cursor_position=len(new)), bypass_readonly=True
            )
        app.invalidate()

    # ── Style ──────────────────────────────────────────────────────────────────
    style = Style.from_dict({
        '':                     '#ffffff bg:#000000',
        'chat-content':         'bg:#050505',
        'header':               'bg:#0084ff #ffffff bold',
        'sidebar':              'bg:#0a0a0a #666666',
        'sidebar.label':        '#444444 bold',
        'sidebar.val':          '#0084ff bold',
        'time':                 '#333333',
        'sender':               '#ffffff bold',
        'me':                   '#0084ff bold',
        'me_text':              '#00aaff',
        'dim':                  '#222222',
        'input-text':           'bg:#000000 #ffffff',
        'status':               'bg:#000000 #555555',
        'status-chat':          'bg:#001a33 #00cfff bold',
        'status-warn':          'bg:#1a0a00 #ffaa00 bold',
        'status-reconnect':     'bg:#1a0000 #ff6666 bold',
        'modal':                'bg:#111111 #ffffff',
        'modal-border':         '#0084ff bold',
        'modal-warn':           'bg:#1a0a00 #ffcc88',
        'modal-border-warn':    '#ffaa00 bold',
        'link':                 '#00cfff bold underline',
        'frame.border':         '#333333',
        'focused frame.border': '#0084ff bold',
        # Mention highlight
        'mention-sender':       '#ffcc00 bold',
        'mention-text':         '#ffcc00',
    })

    # ── Sidebar Kiri ───────────────────────────────────────────────────────────
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

    # ── Chat Mode Indicator ────────────────────────────────────────────────────
    def get_chat_top_indicator():
        if focus_mode[0] == "chat":
            if new_msg_count[0] > 0:
                n = new_msg_count[0]
                return f" ▼ {n} new message{'s' if n>1 else ''} — End to jump "
            return " ▌ CHAT MODE — TAB: back to input │ Ctrl+X: exit "
        return ""

    chat_mode_indicator = Window(
        height=1,
        content=FormattedTextControl(
            text=lambda: (
                FormattedText([("class:status-chat", get_chat_top_indicator())])
                if focus_mode[0] == "chat"
                else FormattedText([("class:dim", "")])
            )
        ),
    )

    # ── Layout ─────────────────────────────────────────────────────────────────
    chat_panel = HSplit([
        chat_mode_indicator,
        chat_area,
    ])

    body = VSplit([
        Window(width=25, content=FormattedTextControl(left_side), style="class:sidebar"),
        Window(width=1, char="│", style="class:dim"),
        chat_panel,
        Window(width=1, char="│", style="class:dim"),
        Window(width=35, content=right_sidebar_area.control, style="class:sidebar"),
    ])

    def get_status_style():
        if connection_status[0] == "reconnecting": return "class:status-reconnect"
        if connection_status[0] == "offline":      return "class:status-reconnect"
        if purge_confirm[0]:                        return "class:status-warn"
        if focus_mode[0] == "chat":                 return "class:status-chat"
        return "class:status"

    root_container = FloatContainer(
        content=HSplit([
            Window(
                height=1,
                style="class:header",
                content=FormattedTextControl(text=get_header_text),
            ),
            body,
            Window(
                height=1,
                style=get_status_style,
                content=FormattedTextControl(text=get_status_text),
            ),
            input_area,
        ]),
        floats=[
            Float(content=ConditionalContainer(
                content=emoji_modal,
                filter=Condition(lambda: show_emoji_modal[0])
            )),
            Float(content=ConditionalContainer(
                content=help_modal,
                filter=Condition(lambda: show_help_modal[0])
            )),
            Float(content=ConditionalContainer(
                content=purge_modal,
                filter=Condition(lambda: show_purge_modal[0])
            )),
        ]
    )

    app = Application(
        layout=Layout(root_container),
        key_bindings=kb,
        full_screen=True,
        style=style,
        mouse_support=True,
    )

    app.layout.focus(input_area)
    threading.Thread(target=fetch_messages, args=(app,), daemon=True).start()
    app.run()