
import tkinter as tk
from tkinter import messagebox
import requests, threading, time, subprocess, sys, os, winreg
import pystray
from PIL import Image, ImageDraw
from win10toast import ToastNotifier

# منابع پروکسی
PROXY_SOURCES = [
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
]

CHECK_URL = "https://www.google.com"
toaster = ToastNotifier()

current_proxy = None
stop_flag = False
mode = None  # 'chrome' یا 'windows'

def fetch_proxies():
    proxies = []
    for url in PROXY_SOURCES:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for line in r.text.splitlines():
                    if ":" in line:
                        proxies.append(line.strip())
        except:
            pass
    return proxies

def test_proxy(proxy):
    try:
        r = requests.get(CHECK_URL, proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=5)
        return r.status_code == 200
    except:
        return False

def set_system_proxy(proxy):
    try:
        internet_settings = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                           r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                                           0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(internet_settings, "ProxyEnable", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(internet_settings, "ProxyServer", 0, winreg.REG_SZ, proxy)
        winreg.CloseKey(internet_settings)
    except Exception as e:
        print("Error setting system proxy:", e)

def start_chrome_with_proxy(proxy):
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    if os.path.exists(chrome_path):
        subprocess.Popen([chrome_path, f"--proxy-server=http://{proxy}"])
    else:
        messagebox.showerror("Chrome not found", "Google Chrome executable not found.")

def monitor_connection():
    global current_proxy, stop_flag
    while not stop_flag:
        try:
            r = requests.get(CHECK_URL, timeout=5)
            if r.status_code != 200:
                raise Exception("Bad status")
        except:
            proxy = find_and_set_proxy(mode)
            if proxy:
                current_proxy = proxy
                toaster.show_toast("Proxy Updated", f"New proxy set: {proxy}", duration=5)
        time.sleep(10)

def find_and_set_proxy(selected_mode):
    proxies = fetch_proxies()
    for proxy in proxies:
        if test_proxy(proxy):
            if selected_mode == "windows":
                set_system_proxy(proxy)
            elif selected_mode == "chrome":
                start_chrome_with_proxy(proxy)
            return proxy
    return None

def start_app(selected_mode):
    global current_proxy, stop_flag, mode
    mode = selected_mode
    stop_flag = False
    current_proxy = find_and_set_proxy(selected_mode)
    if current_proxy:
        toaster.show_toast("Proxy Connected", f"Connected via {current_proxy}", duration=5)
        threading.Thread(target=monitor_connection, daemon=True).start()
    else:
        toaster.show_toast("Proxy Failed", "No working proxy found", duration=5)

def on_quit(icon, item):
    global stop_flag
    stop_flag = True
    icon.stop()
    root.quit()

def setup_tray():
    icon_image = Image.new('RGB', (64, 64), "blue")
    dc = ImageDraw.Draw(icon_image)
    dc.rectangle([0, 0, 64, 64], fill="blue")
    menu = pystray.Menu(
        pystray.MenuItem("Quit", on_quit)
    )
    icon = pystray.Icon("proxy_tray", icon_image, "Proxy App", menu)
    icon.run()

def start_and_hide(selected_mode):
    root.withdraw()
    threading.Thread(target=start_app, args=(selected_mode,), daemon=True).start()
    threading.Thread(target=setup_tray, daemon=True).start()

# GUI
root = tk.Tk()
root.title("Proxy Finder (Iran Edition)")
root.geometry("300x150")

lbl = tk.Label(root, text="Choose proxy mode:")
lbl.pack(pady=10)

btn1 = tk.Button(root, text="Set for Chrome Only", command=lambda: start_and_hide("chrome"))
btn1.pack(pady=5)

btn2 = tk.Button(root, text="Set for Windows (System-wide)", command=lambda: start_and_hide("windows"))
btn2.pack(pady=5)

root.mainloop()
