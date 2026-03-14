import requests
import json
from datetime import datetime
from utils import load_config, get_hw_id

def format_date(ts):
    if not ts or ts == 0:
        return "N/A"
    try:
        return datetime.fromtimestamp(ts).strftime('%d %b %Y')
    except:
        return "—"

def run(args):
    raw_url = load_config()
    if not raw_url:
        print("\033[31m[!] ERROR: No active server connection.\033[0m")
        return

    url = raw_url.rstrip('/')
    pin = get_hw_id()

    print("\n \033[1;34mXTERMCHAT BOT SERVICES\033[0m")
    print(" \033[2m" + "━"*75 + "\033[0m")

    try:
        res = requests.get(f"{url}/bot/list", params={"pin": pin}, timeout=5)

        if res.status_code == 400:
            print(" \033[31m[!] ERROR: PIN required.\033[0m")
            return
        if res.status_code != 200:
            print(f" \033[31m[!] SERVER_ERROR: {res.status_code}\033[0m")
            return

        bots = res.json().get("bots", [])

        if not bots:
            print(" \033[33m No bots registered yet.\033[0m")
            print(f" \033[2m Run 'xtc start:bot' to set one up.\033[0m")
        else:
            # Header
            header = (
                f" \033[1m"
                f"{'ID':<5} "
                f"{'NAME':<12} "
                f"{'ROOM':<16} "
                f"{'STATUS':<10} "
                f"{'TASKS':<30} "
                f"{'STARTED'}"
                f"\033[0m"
            )
            print(header)
            print(" \033[2m" + "─"*75 + "\033[0m")

            active_count  = 0
            stopped_count = 0

            for b in bots:
                bot_id  = str(b.get("id", "?"))
                name    = b.get("name", "?")[:10]
                room    = b.get("room", "?")[:14]
                status  = b.get("status", "unknown")
                started = format_date(b.get("created_at", 0))

                # Parse tasks
                tasks_raw = b.get("tasks", [])
                if isinstance(tasks_raw, str):
                    try:    tasks_raw = json.loads(tasks_raw)
                    except: tasks_raw = []
                task_names = ", ".join(t.get("id", "?") for t in tasks_raw)[:28]

                # Status color
                if status == "active":
                    status_str = "\033[32m● ACTIVE \033[0m"
                    active_count += 1
                elif status == "stopped":
                    status_str = "\033[2m○ STOPPED\033[0m"
                    stopped_count += 1
                else:
                    status_str = f"\033[33m? {status[:7].upper()}\033[0m"

                row = (
                    f" \033[33m{bot_id:<5}\033[0m"
                    f"\033[1m{name:<12}\033[0m"
                    f"\033[34m@{room:<15}\033[0m"
                    f"{status_str:<10} "
                    f"\033[2m{task_names:<30}\033[0m"
                    f"\033[2m{started}\033[0m"
                )
                print(row)

            print(" \033[2m" + "─"*75 + "\033[0m")
            print(
                f" Total: {len(bots)} bot(s) registered  ·  "
                f"\033[32m{active_count} active\033[0m  ·  "
                f"\033[2m{stopped_count} stopped\033[0m"
            )

    except Exception as e:
        print(f" \033[31m[!] CONNECTION_FAILED\033[0m")
        print(f" \033[2mError: {str(e)}\033[0m")

    print(" \033[2m" + "━"*75 + "\033[0m")
    print(" \033[2m start:bot  ·  stop:bot <id>\033[0m\n")