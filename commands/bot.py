"""
bot.py — XtermChat Bot Command
Dipanggil dari xtc.py saat user menjalankan: xtc start:bot

Flow:
  1. Tampilkan daftar room dari server
  2. User pilih room tujuan alert
  3. Tampilkan semua task yang tersedia
  4. User pilih task (bisa multiple)
  5. Konfigurasi per task (interval, target URL, dll)
  6. Simpan config ke xtc.db via POST /bot/register
  7. Minta server spawn bot_runner.py via POST /bot/start
"""

import os
import sys
import json
import socket
import getpass
import requests
from datetime import datetime

from utils import load_config, clean_arg, get_hw_id

# ─── Warna ────────────────────────────────────────────────────────────────────
def B(t):  return f"\033[1;34m{t}\033[0m"
def W(t):  return f"\033[1m{t}\033[0m"
def D(t):  return f"\033[2m{t}\033[0m"
def G(t):  return f"\033[32m{t}\033[0m"
def R(t):  return f"\033[31m{t}\033[0m"
def Y(t):  return f"\033[33m{t}\033[0m"
def C(t):  return f"\033[36m{t}\033[0m"

# ─── Semua task yang tersedia ──────────────────────────────────────────────────
AVAILABLE_TASKS = [
    {
        "id":    "resource",
        "label": "Resource Monitor",
        "desc":  "CPU, RAM, Disk usage — alert if above threshold",
        "needs": ["interval", "cpu_threshold", "ram_threshold", "disk_threshold"],
    },
    {
        "id":    "process",
        "label": "Process Monitor",
        "desc":  "Watch if a process/service dies, with optional auto-restart",
        "needs": ["interval", "process_name", "auto_restart"],
    },
    {
        "id":    "uptime",
        "label": "Uptime Watchdog",
        "desc":  "Ping a URL every N minutes — alert if down",
        "needs": ["interval", "target_url"],
    },
    {
        "id":    "port",
        "label": "Port Checker",
        "desc":  "Verify that specific ports are open on this server",
        "needs": ["interval", "ports"],
    },
    {
        "id":    "traffic",
        "label": "Traffic Monitor",
        "desc":  "Network bandwidth in/out — report usage periodically",
        "needs": ["interval", "interface"],
    },
    {
        "id":    "ssl",
        "label": "SSL Cert Checker",
        "desc":  "Alert N days before SSL certificate expires",
        "needs": ["interval", "ssl_domain", "ssl_warn_days"],
    },
    {
        "id":    "log",
        "label": "Log Watcher",
        "desc":  "Tail a log file and send lines matching a keyword",
        "needs": ["log_file", "log_keyword"],
    },
    {
        "id":    "disk_clean",
        "label": "Disk Cleanup Alert",
        "desc":  "Warn when disk fills up, list top space consumers",
        "needs": ["interval", "disk_threshold"],
    },
    {
        "id":    "schedule",
        "label": "Scheduled Report",
        "desc":  "Send a daily server summary at a set time",
        "needs": ["report_time"],
    },
    {
        "id":    "deploy",
        "label": "Deployment Hook",
        "desc":  "Notify room when deploy.sh calls xtc-bot (webhook)",
        "needs": [],
    },
    {
        "id":    "backup",
        "label": "Backup Notifier",
        "desc":  "Confirm backup success/fail from your backup script",
        "needs": [],
    },
    {
        "id":    "custom",
        "label": "Custom Command",
        "desc":  "Run any shell command and send output to room",
        "needs": ["interval", "shell_command"],
    },
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def header():
    print()
    print(B("┌──────────────────────────────────────┐"))
    print(B("│") + W("   XTERMCHAT  ·  BOT SETUP            ") + B("│"))
    print(B("└──────────────────────────────────────┘"))
    print()

def ask(prompt, default=""):
    d = f" [{default}]" if default else ""
    try:
        val = input(f"  {B('›')} {prompt}{D(d)}: ").strip()
        return val if val else default
    except KeyboardInterrupt:
        print("\n\n  " + D("Aborted."))
        sys.exit(0)

def ask_int(prompt, default):
    while True:
        val = ask(prompt, str(default))
        try:
            return int(val)
        except ValueError:
            print(f"  {R('[!]')} Please enter a number.")

def send_message(url, room, bot_name, pin, content):
    """Kirim pesan test ke room."""
    try:
        res = requests.post(f"{url}/send", json={
            "room":     room,
            "user":     bot_name,
            "pin":      pin,
            "content":  content,
            "password": "",
        }, timeout=8)
        return res.status_code == 201
    except Exception:
        return False

# ─── Step 1: Pilih room ───────────────────────────────────────────────────────

def pick_room(url):
    print(f"  {B('▸')} {W('SELECT ROOM')}  {D('(room that will receive bot alerts)')}\n")
    try:
        res = requests.get(f"{url}/rooms", timeout=5)
        if res.status_code != 200:
            print(R("  [!] Cannot fetch rooms from server."))
            sys.exit(1)
        rooms = res.json().get("rooms", [])
    except Exception as e:
        print(R(f"  [!] Connection failed: {e}"))
        sys.exit(1)

    if not rooms:
        print(Y("  [!] No rooms found. Create a room first: xtc create:room @alerts"))
        sys.exit(1)

    for i, r in enumerate(rooms, 1):
        lock = Y("LOCKED") if r.get("has_password") else G("OPEN  ")
        print(f"    {D(str(i)+'.'):5} {B('@'+r['name'][:20]):25} {lock}  {D('by '+r.get('creator','?')[:10])}")

    print()
    while True:
        choice = ask("Select room number", "1")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(rooms):
                return rooms[idx]["name"]
        except ValueError:
            pass
        print(R("  [!] Invalid choice."))

# ─── Step 2: Pilih tasks ──────────────────────────────────────────────────────

def pick_tasks():
    print()
    print(f"  {B('▸')} {W('SELECT BOT TASKS')}  {D('(comma-separated numbers, e.g. 1,3,5)')}\n")

    for i, t in enumerate(AVAILABLE_TASKS, 1):
        num   = D(f"{i}.")
        label = W(f"{t['label']:<25}")
        desc  = D(t['desc'])
        print(f"    {num:5} {label}  {desc}")

    print()
    while True:
        raw = ask("Select tasks")
        try:
            indices  = [int(x.strip()) - 1 for x in raw.split(",") if x.strip()]
            selected = [AVAILABLE_TASKS[i] for i in indices if 0 <= i < len(AVAILABLE_TASKS)]
            if selected:
                return selected
        except (ValueError, IndexError):
            pass
        print(R("  [!] Invalid selection. Enter numbers like: 1,3,5"))

# ─── Step 3: Konfigurasi per task ─────────────────────────────────────────────

def configure_task(task):
    needs  = task["needs"]
    config = {}

    if "interval" in needs:
        config["interval"] = ask_int(f"Check interval for '{task['label']}' (minutes)", 5)
    if "cpu_threshold" in needs:
        config["cpu_threshold"]  = ask_int("Alert when CPU above (%)", 80)
    if "ram_threshold" in needs:
        config["ram_threshold"]  = ask_int("Alert when RAM above (%)", 85)
    if "disk_threshold" in needs:
        config["disk_threshold"] = ask_int("Alert when Disk above (%)", 90)
    if "process_name" in needs:
        config["process_name"] = ask("Process name to watch (e.g. nginx, gunicorn)")
    if "auto_restart" in needs:
        val = ask("Auto-restart if process dies? (yes/no)", "no").lower()
        config["auto_restart"] = val in ("yes", "y")
    if "target_url" in needs:
        config["target_url"] = ask("URL to monitor (e.g. https://myapp.com)")
    if "ports" in needs:
        raw = ask("Ports to check (comma-separated, e.g. 80,443,8080)", "8080")
        config["ports"] = [int(p.strip()) for p in raw.split(",") if p.strip().isdigit()]
    if "interface" in needs:
        config["interface"] = ask("Network interface (e.g. eth0, ens3)", "eth0")
    if "ssl_domain" in needs:
        config["ssl_domain"] = ask("Domain to check SSL (e.g. myapp.com)")
    if "ssl_warn_days" in needs:
        config["ssl_warn_days"] = ask_int("Warn when cert expires in N days", 30)
    if "log_file" in needs:
        config["log_file"] = ask("Path to log file (e.g. /var/log/nginx/error.log)")
    if "log_keyword" in needs:
        config["log_keyword"] = ask("Keyword to watch for (e.g. ERROR, CRITICAL)", "ERROR")
    if "report_time" in needs:
        config["report_time"] = ask("Daily report time (HH:MM, 24h format)", "08:00")
    if "shell_command" in needs:
        config["shell_command"] = ask("Shell command to run (e.g. df -h /)")

    return config

# ─── Step 4: Simpan config ke server ──────────────────────────────────────────

def save_bot_config(url, bot_name, pin, room, tasks_config):
    """POST /bot/register → server simpan ke tabel bots di xtc.db"""
    try:
        res = requests.post(f"{url}/bot/register", json={
            "name":  bot_name,
            "pin":   pin,
            "room":  room,
            "host":  socket.gethostname(),
            "tasks": tasks_config,
        }, timeout=8)

        if res.status_code in (200, 201):
            return res.json().get("bot_id")
        else:
            print(R(f"  [!] Server error: {res.status_code} — {res.text[:100]}"))
            return None
    except Exception as e:
        print(R(f"  [!] Connection failed: {e}"))
        return None

# ─── Step 5: Minta server spawn bot_runner.py ─────────────────────────────────

def request_bot_start(url, bot_id, pin):
    """
    POST /bot/start → server spawn bot_runner.py di background VPS.
    bot_runner.py harus ada di folder xtc-server di VPS.
    """
    try:
        res = requests.post(f"{url}/bot/start", json={
            "bot_id": bot_id,
            "pin":    pin,
        }, timeout=15)

        if res.status_code == 200:
            data = res.json()
            return data.get("pid")
        else:
            print(R(f"  [!] Server error: {res.status_code} — {res.text[:100]}"))
            return None
    except Exception as e:
        print(R(f"  [!] Connection failed: {e}"))
        return None

# ─── Main run ─────────────────────────────────────────────────────────────────

def run(args):
    raw_url = load_config()
    if not raw_url:
        print(R("  [!] ERROR: No server connection. Run 'xtc connect @ip' first."))
        return

    url      = raw_url.rstrip("/")
    bot_pin  = get_hw_id()
    bot_user = getpass.getuser()[:5].upper()

    header()

    # ── 1. Pilih room ──────────────────────────────────────────────────────────
    room = pick_room(url)
    print(f"\n  {G('✓')} Room selected: {B('@'+room)}\n")

    # ── 2. Nama bot ────────────────────────────────────────────────────────────
    print(f"  {B('▸')} {W('BOT IDENTITY')}\n")
    bot_name = ask("Bot name (shown as sender in room)", f"{bot_user}-BOT").upper()[:10]
    print()

    # ── 3. Pilih tasks ─────────────────────────────────────────────────────────
    selected_tasks = pick_tasks()
    print(f"\n  {G('✓')} {len(selected_tasks)} task(s) selected.\n")

    # ── 4. Konfigurasi tiap task ───────────────────────────────────────────────
    print(f"  {B('▸')} {W('CONFIGURE TASKS')}\n")
    tasks_config = []
    for task in selected_tasks:
        print(f"  {D('─'*36)}")
        print(f"  {W(task['label'])}  {D(task['desc'])}\n")
        cfg = configure_task(task)
        tasks_config.append({"id": task["id"], "label": task["label"], "config": cfg})

    # ── 5. Preview & konfirmasi ────────────────────────────────────────────────
    print()
    print(f"  {B('▸')} {W('SUMMARY')}\n")
    print(f"  {D('Bot name')}   {W(bot_name)}")
    print(f"  {D('Room')}       {B('@'+room)}")
    print(f"  {D('Server')}     {url}")
    print(f"  {D('Tasks')}      {', '.join(t['label'] for t in selected_tasks)}")
    print()

    confirm = ask("Save and start bot? (yes/no)", "yes").lower()
    if confirm not in ("yes", "y"):
        print(f"\n  {D('Aborted.')}\n")
        return

    # ── 6. Simpan config ke server ─────────────────────────────────────────────
    print()
    print(f"  {D('Saving configuration to server...')}")
    bot_id = save_bot_config(url, bot_name, bot_pin, room, tasks_config)

    if not bot_id:
        print(R("  [!] Failed to save bot config. Check server logs."))
        return

    print(f"  {G('✓')} Config saved  {D('(bot_id: '+str(bot_id)+')')}")

    # ── 7. Minta server start bot_runner.py ────────────────────────────────────
    print(f"  {D('Requesting server to start bot process...')}")
    pid = request_bot_start(url, bot_id, bot_pin)

    if not pid:
        print(R("  [!] Failed to start bot on server."))
        print(f"  {D('Make sure bot_runner.py is in the xtc-server folder on your VPS.')}")
        return

    print(f"  {G('✓')} Bot started on server  {D('(PID: '+str(pid)+')')}")

    # ── 8. Kirim pesan ke room ─────────────────────────────────────────────────
    test_msg = (
        f":robot: {bot_name} is now online [{datetime.now().strftime('%d %b %Y %H:%M:%S')}]\n"
        f"  Tasks  : {', '.join(t['label'] for t in selected_tasks)}\n"
        f"  Room   : #{room}"
    )
    send_message(url, room, bot_name, bot_pin, test_msg)

    print()
    print(f"  {B('▸')} {W('BOT IS RUNNING ON SERVER')}")
    print(f"  {D('bot_id')}    {W(str(bot_id))}")
    print(f"  {D('Stop with')} {C('xtc stop:bot '+str(bot_id))}")
    print()