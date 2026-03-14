"""
bot_stop.py — Stop a running XtermChat bot
Dipanggil dari xtc.py saat user menjalankan:

  xtc stop:bot <id>   — stop bot tertentu
  xtc stop:bot        — list semua bot milik kamu
"""

import sys
import requests
from datetime import datetime
from utils import load_config, get_hw_id

def B(t): return f"\033[1;34m{t}\033[0m"
def W(t): return f"\033[1m{t}\033[0m"
def G(t): return f"\033[32m{t}\033[0m"
def R(t): return f"\033[31m{t}\033[0m"
def D(t): return f"\033[2m{t}\033[0m"
def Y(t): return f"\033[33m{t}\033[0m"


def run(args):
    raw_url = load_config()
    if not raw_url:
        print(R("  [!] No server connection. Run 'xtc connect @ip' first."))
        return

    url = raw_url.rstrip("/")
    pin = get_hw_id()

    # Tidak ada args → tampilkan list bot
    if not args:
        list_bots(url, pin)
        return

    bot_id = args[0].lstrip("#")

    # Konfirmasi
    print(f"\n  {Y('Stop bot')} {B('#'+bot_id)}?")
    confirm = input(f"  {D('›')} Confirm? (yes/no) [no]: ").strip().lower()
    if confirm not in ("yes", "y"):
        print(f"  {D('Cancelled.')}\n")
        return

    # Kirim stop request ke server
    try:
        res = requests.post(f"{url}/bot/kill", json={
            "bot_id": int(bot_id),
            "pin":    pin,
        }, timeout=10)

        data = res.json()

        if res.status_code == 200:
            pid = data.get("pid", "?")
            print(f"\n  {G('✓')} Bot {B('#'+bot_id)} stopped  {D('(PID: '+str(pid)+')')}\n")
        elif res.status_code == 404:
            print(R(f"\n  [!] Bot #{bot_id} not found.\n"))
        elif res.status_code == 403:
            print(R(f"\n  [!] Unauthorized — you are not the owner of this bot.\n"))
        elif res.status_code == 409:
            print(f"\n  {D('Bot #'+bot_id+' was already stopped.')}\n")
        else:
            print(R(f"\n  [!] Server error: {res.status_code} — {data.get('message','')}\n"))

    except Exception as e:
        print(R(f"\n  [!] Connection failed: {e}\n"))


def list_bots(url, pin):
    """Tampilkan semua bot yang terdaftar milik PIN ini."""
    try:
        res = requests.get(f"{url}/bot/list", params={"pin": pin}, timeout=5)
        if res.status_code != 200:
            print(R(f"  [!] Server error: {res.status_code}"))
            return

        bots = res.json().get("bots", [])

        if not bots:
            print(f"\n  {D('No bots registered.')}")
            print(f"  {D('Start one with: xtc start:bot')}\n")
            return

        print()
        print(f"  {B('▸')} {W('YOUR BOTS')}\n")
        print(f"  {D('ID'):6} {D('NAME'):12} {D('ROOM'):16} {D('STATUS'):12} {D('TASKS')}")
        print(f"  {D('─'*70)}")

        for b in bots:
            bot_id = str(b.get("id", "?"))
            name   = b.get("name", "?")[:10]
            room   = b.get("room", "?")[:14]
            status = b.get("status", "unknown")
            tasks  = b.get("tasks", [])

            if isinstance(tasks, str):
                import json
                try:    tasks = json.loads(tasks)
                except: tasks = []

            task_names = ", ".join(t.get("id", "?") for t in tasks)[:28]

            # Warna status
            if status == "active":
                status_str = G("● RUNNING")
            elif status == "stopped":
                status_str = D("○ STOPPED")
            else:
                status_str = Y(f"? {status.upper()}")

            created = b.get("created_at", 0)
            try:
                created_str = datetime.fromtimestamp(created).strftime("%d %b %Y")
            except Exception:
                created_str = "—"

            print(
                f"  {D('#'+bot_id):6} "
                f"{W(name):12} "
                f"{B('@'+room):16} "
                f"{status_str:12} "
                f"{D(task_names)}"
            )

        print()
        print(f"  {D('Stop a bot:')}  {B('xtc stop:bot <id>')}")
        print()

    except Exception as e:
        print(R(f"  [!] Error: {e}"))