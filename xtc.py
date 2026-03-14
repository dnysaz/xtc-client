#!/usr/bin/env python3
import sys
import os
import shutil
import subprocess
from commands import connect, disconnect, status, create, delete, chat, listRooms

# ─── Helpers ──────────────────────────────────────────────────────────────────

def W(text):  return f"\033[1m{text}\033[0m"          # Bold white
def D(text):  return f"\033[2m{text}\033[0m"          # Dim
def B(text):  return f"\033[1;34m{text}\033[0m"       # Bold blue
def C(text):  return f"\033[34m{text}\033[0m"         # Blue (commands)
def R(text):  return f"\033[31m{text}\033[0m"         # Red (errors only)

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

    # Commands
    commands = [
        ("connect",      "Connect client to a server"),
        ("disconnect",   "Remove saved server config"),
        ("status",       "Check server connection"),
        ("list:rooms",   "List all available rooms"),
        ("create:room",  "Create a new room"),
        ("delete:room",  "Delete a room permanently"),
        ("start:chat",   "Open interactive chat"),
        ("start:web",    "Open web interface"),
    ]

    print(f"  {B('▸')} {W('COMMANDS')}")
    for cmd, desc in commands:
        print(f"    {B(f'{cmd:<16}')} {D(desc)}")

    # Examples
    print(f"\n  {B('▸')} {W('EXAMPLES')}")
    examples = [
        "xtc connect @123.123.123.123:8080",
        "xtc status",
        "xtc list:rooms",
        "xtc create:room",
        "xtc start:chat @general",
        "xtc delete:room @general",
        "xtc start:web",
    ]
    for ex in examples:
        parts = ex.split(" ", 2)
        line  = f"    {D(parts[0])} {C(parts[1])}"
        if len(parts) > 2:
            line += f" {W(parts[2])}"
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