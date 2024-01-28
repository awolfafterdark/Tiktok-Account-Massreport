import json, os, time, random, threading, re, sys
import requests
from requests.exceptions import ProxyError, ConnectTimeout, ReadTimeout, ConnectionError
from fake_useragent import UserAgent

try:
    import pystyle
    import colorama
    import httpx
except ModuleNotFoundError:
    os.system("pip install pystyle")
    os.system("pip install colorama")
    os.system("pip install httpx")
    os.system("pip install fake_useragent")

from pystyle import Write, System, Colorate, Colors
from colorama import Fore, Style

# Color definitions
red = Fore.RED
yellow = Fore.YELLOW
green = Fore.GREEN
blue = Fore.BLUE
orange = Fore.RED + Fore.YELLOW
pretty = Fore.LIGHTMAGENTA_EX + Fore.LIGHTCYAN_EX
magenta = Fore.MAGENTA
lightblue = Fore.LIGHTBLUE_EX
cyan = Fore.CYAN
gray = Fore.LIGHTBLACK_EX + Fore.WHITE
reset = Fore.RESET
pink = Fore.LIGHTGREEN_EX + Fore.LIGHTMAGENTA_EX
dark_green = Fore.GREEN + Style.BRIGHT

# Global variables
success = 0
failed = 0
generated_agents = 0
total = 1

start = time.time()

# Function definitions
def save_proxies(proxies):
    with open("proxies.txt", "w") as file:
        file.write("\n".join(proxies))

def get_proxies():
    with open('proxies.txt', 'r', encoding='utf-8') as f:
        proxies = f.read().splitlines()
    if not proxies:
        proxy_log = None
    else:
        proxy = random.choice(proxies)
        proxy_log = {
            "http://": f"http://{proxy}", "https://": f"http://{proxy}"
        }
    try:
        url = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all"
        response = httpx.get(url, proxies=proxy_log, timeout=60)

        if response.status_code == 200:
            proxies = response.text.splitlines()
            save_proxies(proxies)
        else:
            time.sleep(1)
            get_proxies()
    except (httpx.ProxyError, httpx.ReadError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError, httpx.ProtocolError):
        get_proxies()

def check_proxies_file():
    file_path = "proxies.txt"
    if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
        get_proxies()

# Load configuration
with open(f"config.json") as f:
    data = json.load(f)
    if data["proxy_scraper"] in ["y", "yes"]:
        check_proxies_file()

def get_time_rn():
    return time.strftime("%H:%M:%S", time.localtime())

def mass_report():
    global success, total, failed, generated_agents
    proxy = random.choice(open("proxies.txt", "r").readlines()).strip() if len(open("proxies.txt", "r").readlines()) != 0 else None
    session = requests.Session()
    user_agent = UserAgent().random
    session.headers = {'User-Agent': user_agent}

    if "@" in proxy:
        user_pass, ip_port = proxy.split("@")
        user, password = user_pass.split(":")
        ip, port = ip_port.split(":")
        proxy_string = f"http://{user}:{password}@{ip}:{port}"
    else:
        ip, port = proxy.split(":")
        proxy_string = f"http://{ip}:{port}"

    session.proxies = {
        "http": proxy_string,
        "https": proxy_string
    }

    with open(f"config.json") as f:
        data = json.load(f)
        url = data['report_url']
        report_types = data['report_types']
        report_type = next((code for type, code in report_types.items() if data.get(type) in ['y', 'yes']), None)

    output_lock = threading.Lock()
    try:
        match_reason = re.search(r'reason=(\d+)', url)
        match_nickname = re.search(r'nickname=([^&]+)', url)
        match_owner_id = re.search(r'owner_id=([^&]+)', url)
        if match_nickname and match_owner_id and match_reason:
            username = match_nickname.group(1)
            iduser = match_owner_id.group(1)
            reason_number = match_reason.group(1)
            new_url = url.replace(f"reason={reason_number}", f"reason={report_type}")
            report = session.get(new_url)
            if "Thanks for your feedback" in report.text or report.status_code == 200:
                with output_lock:
                    time_rn = get_time_rn()
                    print(f"[ {magenta}{time_rn}{reset} ] | ( {green}+{reset} ) {blue}Reported successfully to {username} ~ {iduser}\n")
                    success += 1
                    total += 1
            else:
                with output_lock:
                    time_rn = get_time_rn()
                    print(f"[ {magenta}{time_rn}{reset} ] | ( {red}-{reset} ) {yellow}Cannot report to {username} ~ {iduser}\n")
                    failed += 1
                    total += 1
    except Exception as e:
        failed += 1
        total += 1

def mass_report_thread():
    mass_report()

def check_ui():
    output_lock = threading.Lock()
    while True:
        success_rate = round(success/total*100,2) if total > 0 else 0
        System.Clear()
        with output_lock:
            Write.Print(f"\nReports Sent: {success} ~ Failed: {failed} ~ Success Rate: {success_rate}%\n", Colors.blue_to_red, interval=0.000)
            time.sleep(10)

num_threads = data['threads']
threads = []

with threading.Lock():
    for _ in range(num_threads - 1):
        thread = threading.Thread(target=mass_report_thread)
        thread.start()
        threads.append(thread)

    check_ui_thread = threading.Thread(target=check_ui)
    check_ui_thread.start()
    threads.append(check_ui_thread)

    for thread in threads:
        thread.join()
