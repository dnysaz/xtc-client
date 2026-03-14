#!/usr/bin/env python3
import sys
import os
import shutil
import subprocess
from commands import connect, disconnect, status, create, delete, chat, listRooms, bot, bot_stop

# ─── Helpers ──────────────────────────────────────────────────────────────────

def W(text):  return f"\033[1m{text}\033[0m"
def D(text):  return f"\033[2m{text}\033[0m"
def B(text):  return f"\033[1;34m{text}\033[0m"
def C(text):  return f"\033[34m{text}\033[0m"
def R(text):  return f"\033[31m{text}\033[0m"

def terminal_width():
    return min(shutil.get_terminal_size().columns, 64)

# ─── Help ─────────────────────────────────────────────────────────────────────

def show_help():
    w = terminal_width()

    # Header
    print()
    print(W("┌" + "─" * (w - 2) + "┐"))
    print(W("│") + " X T E R M  C H A T ".center(w - 2) + W("│"))
    print(W("│") + D(" For Those Who Speak Terminal. ".center(w - 2)) + W("│"))
    print(W("└" + "─" * (w - 2) + "┘"))

    # Meta
    print(f"\n  {D('TYPE')}  {W('TERMINAL-CHAT')}   {D('VER')}  {W('1.0')}   {D('HOST')}  {W('SELF-HOSTED')}")

    # Usage
    print(f"\n  {B('▸')} {W('USAGE')}")
    print(f"    {C('xtc')} <command> [args]\n")

    # Commands — dikelompokkan per kategori
    groups = [
        ("CONNECTION", [
            ("connect",     "Connect client to a server"),
            ("disconnect",  "Remove saved server config"),
            ("status",      "Check server connection"),
        ]),
        ("ROOMS", [
            ("list:rooms",  "List all available rooms"),
            ("create:room", "Create a new room"),
            ("delete:room", "Delete a room permanently"),
        ]),
        ("CHAT", [
            ("start:chat",  "Open interactive chat"),
            ("start:web",   "Open web interface"),
        ]),
        ("BOT", [
            ("start:bot",   "Start a monitoring bot on this server"),
            ("stop:bot",    "Stop a running bot  (stop:bot <id>)"),
        ]),
    ]

    print(f"  {B('▸')} {W('COMMANDS')}")
    for group_name, cmds in groups:
        print(f"\n    {D(group_name)}")
        for cmd, desc in cmds:
            print(f"    {B(f'{cmd:<16}')} {D(desc)}")

    # Examples
    print(f"\n  {B('▸')} {W('EXAMPLES')}")
    examples = [
        ("xtc connect",    "@123.123.123.123:8080"),
        ("xtc status",     ""),
        ("xtc list:rooms", ""),
        ("xtc create:room",""),
        ("xtc start:chat", "@general"),
        ("xtc delete:room","@general"),
        ("xtc start:web",  ""),
        ("xtc start:bot",  ""),
        ("xtc stop:bot",   "1"),
    ]
    for cmd, arg in examples:
        parts = cmd.split(" ", 1)
        line  = f"    {D(parts[0])} {C(parts[1])}"
        if arg:
            line += f" {W(arg)}"
        print(line)

    # Footer
    print(f"\n" + D("─" * w) + "\n")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        show_help()
        return

    cmd = sys.argv[1]

    if cmd == "connect":
        connect.run(sys.argv[2:])

    elif cmd == "disconnect":
        disconnect.run(sys.argv[2:])

    elif cmd == "status":
        status.run(sys.argv[2:])

    elif cmd == "list:rooms":
        listRooms.run(sys.argv[2:])

    elif cmd == "create:room":
        create.run(sys.argv[2:])

    elif cmd == "delete:room":
        delete.run(sys.argv[2:])

    elif cmd == "start:chat":
        chat.run(sys.argv[2:])

    elif cmd == "start:bot":
        bot.run(sys.argv[2:])

    elif cmd == "stop:bot":
        bot_stop.run(sys.argv[2:])

    elif cmd in ("help", "--help", "-h"):
        show_help()

    elif cmd == "start:web":
        base_path  = os.path.dirname(os.path.realpath(__file__))
        web_script = os.path.join(base_path, "web", "app.py")

        if not os.path.exists(web_script):
            print(R(f"[!] Web module not found: {web_script}"))
            return

        print(f"\n  {B('▸')} Starting web interface...")
        print(f"  {D('URL')}  {W('http://localhost:5000')}\n")

        try:
            subprocess.run(
                [sys.executable, web_script],
                cwd=os.path.join(base_path, "web")
            )
        except KeyboardInterrupt:
            print(f"\n  {D('Web interface stopped.')}\n")

    else:
        print(f"\n  {R('[!]')} {W(cmd)} is not a valid command.\n")
        show_help()


if __name__ == "__main__":
    main()