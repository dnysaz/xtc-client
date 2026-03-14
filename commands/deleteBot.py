"""
deleteBot.py — Delete a registered bot
Usage:
  xtc delete:bot <id>     — hapus bot tertentu by ID
  xtc delete:bot all      — hapus semua bot yang stopped
"""

import requests
import json
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

    # Tidak ada args → tampilkan usage
    if not args:
        print(f"\n  {R('[!]')} Specify a bot ID or 'all'.")
        print(f"  {D('Usage:')}  {B('xtc delete:bot <id>')}")
        print(f"           {B('xtc delete:bot all')}  {D('(delete all stopped bots)')}\n")
        return

    target = args[0].lstrip("#")

    # ── Delete semua yang stopped ──────────────────────────────────────────────
    if target.lower() == "all":
        delete_all_stopped(url, pin)
        return

    # ── Delete by ID ───────────────────────────────────────────────────────────
    # Validasi angka
    if not target.isdigit():
        print(R(f"  [!] Invalid ID '{target}'. Use a number or 'all'."))
        return

    bot_id = int(target)

    # Konfirmasi
    print(f"\n  {Y('Delete bot')} {B('#'+str(bot_id))}?")
    confirm = input(f"  {D('›')} Confirm? (yes/no) [no]: ").strip().lower()
    if confirm not in ("yes", "y"):
        print(f"  {D('Cancelled.')}\n")
        return

    do_delete(url, bot_id, pin)


def do_delete(url, bot_id, pin):
    """Kirim DELETE request ke server untuk satu bot."""
    try:
        res = requests.post(f"{url}/bot/delete", json={
            "bot_id": bot_id,
            "pin":    pin,
        }, timeout=8)

        data = res.json()

        if res.status_code == 200:
            print(f"  {G('✓')} Bot {B('#'+str(bot_id))} deleted.\n")
        elif res.status_code == 403:
            print(R(f"  [!] Unauthorized — not the owner of bot #{bot_id}."))
        elif res.status_code == 404:
            print(R(f"  [!] Bot #{bot_id} not found."))
        elif res.status_code == 409:
            print(Y(f"  [!] Bot #{bot_id} is still ACTIVE. Stop it first: xtc stop:bot {bot_id}"))
        else:
            print(R(f"  [!] Server error: {res.status_code} — {data.get('message','')}"))

    except Exception as e:
        print(R(f"  [!] Connection failed: {e}"))


def delete_all_stopped(url, pin):
    """Ambil semua bot stopped milik PIN ini lalu hapus semuanya."""
    try:
        res = requests.get(f"{url}/bot/list", params={"pin": pin}, timeout=5)
        if res.status_code != 200:
            print(R(f"  [!] Cannot fetch bots: {res.status_code}"))
            return

        bots = res.json().get("bots", [])
        stopped = [b for b in bots if b.get("status") == "stopped"]

        if not stopped:
            print(f"\n  {D('No stopped bots to delete.')}\n")
            return

        print(f"\n  {Y('Delete all stopped bots?')}  {D('('+str(len(stopped))+' bots)')}")
        for b in stopped:
            tasks_raw = b.get("tasks", [])
            if isinstance(tasks_raw, str):
                try:    tasks_raw = json.loads(tasks_raw)
                except: tasks_raw = []
            task_names = ", ".join(t.get("id", "?") for t in tasks_raw)
            print(f"  {D('  #'+str(b['id'])+' '+b['name']+'  @'+b['room']+'  '+task_names)}")

        print()
        confirm = input(f"  {D('›')} Confirm delete all? (yes/no) [no]: ").strip().lower()
        if confirm not in ("yes", "y"):
            print(f"  {D('Cancelled.')}\n")
            return

        print()
        deleted = 0
        for b in stopped:
            try:
                res = requests.post(f"{url}/bot/delete", json={
                    "bot_id": b["id"],
                    "pin":    pin,
                }, timeout=8)
                if res.status_code == 200:
                    print(f"  {G('✓')} Bot {B('#'+str(b['id']))} {D(b['name'])} deleted.")
                    deleted += 1
                else:
                    print(R(f"  [!] Failed to delete #{b['id']}: {res.status_code}"))
            except Exception as e:
                print(R(f"  [!] Error on #{b['id']}: {e}"))

        print(f"\n  {G('✓')} {deleted} bot(s) deleted.\n")

    except Exception as e:
        print(R(f"  [!] Connection failed: {e}"))