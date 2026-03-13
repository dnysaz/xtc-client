#!/usr/bin/env python3
import sys
import shutil
from commands import connect,disconnect,status, create, delete, chat, listRooms 

def get_terminal_width():
    # Mendapatkan lebar terminal agar border tetap rapi
    return shutil.get_terminal_size().columns

def show_help():
    """Menampilkan menu help dengan slogan: For Those Who Speak Terminal."""
    width = min(get_terminal_width(), 64)
    
    # Header Section
    print("\n\033[1;32m" + "┌" + "─"*(width-2) + "┐")
    print("│" + " X T E R M  C H A T ".center(width-2) + "│")
    print("│" + " For Those Who Speak Terminal. ".center(width-2) + "│")
    print("└" + "─"*(width-2) + "┘\033[0m")

    # Status Bar
    print(f" \033[2mTYPE:\033[0m \033[32mTERMINAL-CHAT\033[0m  \033[2m|  VER:\033[0m \033[32m1.0.5\033[0m  \033[2m|  ENCRYPT:\033[0m \033[32mON\033[0m")

    # Usage Section
    print(f"\n \033[1;34m➤\033[0m \033[1mUSAGE:\033[0m")
    print(f"   \033[32m$ xtc <command> [args]\033[0m\n")
    
    # Commands List
    commands = [
        ("connect", "Sync with central gateway"),
        ("disconnect", "Clear current server configuration"),
        ("status", "Check current gateway connection"),
        ("list:rooms", "Display all public chat rooms"),
        ("create:room", "Deploy a new secured room"),
        ("delete:room", "Wipe room & incinerate logs"),
        ("start:chat", "Establish encrypted session"),
    ]
    
    print(" \033[1;34m➤\033[0m \033[1mCOMMANDS:\033[0m")
    for cmd, desc in commands:
        print(f"   \033[1;32m{cmd:15}\033[0m \033[2m{desc}\033[0m")
    
    # Examples Section
    print(f"\n \033[1;34m➤\033[0m \033[1mEXAMPLES:\033[0m")
    print(f"   \033[36mxtc connect @server_ip\033[0m")
    print(f"   \033[36mxtc disconnect @server_ip\033[0m")
    print(f"   \033[36mxtc status\033[0m")
    print(f"   \033[36mxtc list:rooms\033[0m")
    print(f"   \033[36mxtc create:room @myroom\033[0m")
    print(f"   \033[36mxtc create:room @private (password)\033[0m")
    print(f"   \033[36mxtc start:chat @myroom\033[0m")
    print(f"   \033[36mxtc delete:room @myroom\033[0m")
    
    # Footer
    print("\n\033[1;32m" + "─"*width + "\033[0m\n")

def main():
    if len(sys.argv) < 2:
        show_help()
        return

    cmd = sys.argv[1]

    # Command Dispatching
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
    elif cmd in ["help", "--help", "-h"]:
        show_help()
    elif cmd == "start:web":
        import subprocess
        import os
        
        # Mengambil path absolut dari folder tempat xtc.py berada
        # Meskipun dijalankan lewat symlink di /usr/local/bin
        base_path = os.path.dirname(os.path.realpath(__file__))
        web_script = os.path.join(base_path, "web", "app.py")
        
        if not os.path.exists(web_script):
            print(f"\033[31m[!] ERROR: Web module not found at {web_script}\033[0m")
            return

        print("\n\033[1;32m[*] Starting XtermChat Web Gateway...\033[0m")
        print("\033[36m[*] URL: http://localhost:5000\033[0m")
        
        try:
            # Jalankan dengan mengganti directory kerja ke folder web agar Flask tidak bingung
            subprocess.run([sys.executable, web_script], cwd=os.path.join(base_path, "web"))
        except KeyboardInterrupt:
            print("\n\033[31m[*] Web Gateway stopped.\033[0m")
    else:
        print(f"\n\033[1;31m[!] ERROR: '{cmd}' is not a valid operation.\033[0m")
        show_help()

if __name__ == "__main__":
    main()