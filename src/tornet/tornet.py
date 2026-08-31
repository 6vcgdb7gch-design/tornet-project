#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# tornet - Automate IP address changes using Tor
# Author: Fidal
# Copyright (c) 2024 Fidal. All rights reserved.

import argparse
import os
import platform
import signal
import subprocess
import time

import requests
from .utils import install_pip, install_requests, install_tor
from .banner import print_banner

TOOL_NAME = "tornet"

green = "\033[92m"
red = "\033[91m"
white = "\033[97m"
reset = "\033[0m"
cyan = "\033[36m"

def is_arch_linux():
    try:
        return 'arch' in platform.platform().lower()
    except:
        return False

def is_tor_installed():
    try:
        subprocess.check_output('which tor', shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def start_tor_service():
    if platform.system() == "Darwin":
        os.system("brew services start tor")
    elif platform.system() == "Linux":
        os.system("sudo systemctl start tor")

def reload_tor_service():
    if platform.system() == "Darwin":
        # У brew services нет отдельной команды reload
        os.system("brew services restart tor")
    elif platform.system() == "Linux":
        os.system("sudo systemctl reload tor")

def stop_tor_service():
    if platform.system() == "Darwin":
        os.system("brew services stop tor")
    elif platform.system() == "Linux":
        os.system("sudo systemctl stop tor")

def install_pip():
    import importlib.util

    if importlib.util.find_spec("pip") is None:
        raise RuntimeError(
            "pip не установлен. Установите его вручную "
            "в активном виртуальном окружении."
        )

def print_start_message():
    print(f"{white} [{green}+{white}]{green} Tor service started. Please wait a minute for Tor to connect.")
    print(f"{white} [{green}+{white}]{green} Make sure to configure your browser to use Tor for anonymity.")

def ma_ip():
    return ma_ip_tor()


def is_tor_running():
    try:
        with socket.create_connection(("127.0.0.1", 9050), timeout=3):
            return True
    except OSError:
        return False

def ma_ip_tor():
    url = 'https://api.ipify.org'
    proxies = {
        'http': 'socks5://127.0.0.1:9050',
        'https': 'socks5://127.0.0.1:9050'
    }
    try:
        response = requests.get(url, proxies=proxies)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException:
        print(f'{white} [{red}!{white}] {red}Having trouble connecting to the Tor network. wait a minute.{reset}')
        return None

def ma_ip_normal():
    try:
        response = requests.get('https://api.ipify.org')
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException:
        print(f'{white} [{red}!{white}] {red}Having trouble fetching the IP address. Please check your internet connection.{reset}')
        return None

def change_ip():
    try:
        from stem import Signal
        from stem.control import Controller

        with Controller.from_port(
            address="127.0.0.1",
            port=9051,
        ) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)

        time.sleep(10)

        new_ip = ma_ip_tor()

        if new_ip:
            return new_ip

    except Exception as error:
        print(f"Не удалось сменить Tor-цепочку: {error}")

    return None

def change_ip_repeatedly(interval, count):
    if count == 0:
        while True:
            time.sleep(interval)
            new_ip = change_ip()
            if new_ip:
                print_ip(new_ip)
    else:
        for _ in range(count):
            time.sleep(interval)
            new_ip = change_ip()
            if new_ip:
                print_ip(new_ip)

def print_ip(ip):
    print(f'{white} [{green}+{white}]{green} Your IP has been changed to {white}:{green} {ip}')

def auto_fix():
    install_pip()
    install_requests()
    install_tor()
    os.system("pip3 install --upgrade tornet")

def stop_services():
    stop_tor_service()
    os.system(f"pkill -f {TOOL_NAME} > /dev/null 2>&1")
    print(f"{white} [{green}+{white}]{green} Tor services and {TOOL_NAME} processes stopped.{reset}")

def signal_handler(sig, frame):
    stop_services()
    print(f"\n{white} [{red}!{white}] {red}Program terminated by user.{reset}")
    exit(0)

def check_internet_connection():
    while True:
        time.sleep(1)
        try:
            requests.get('https://www.google.com', timeout=1)
        except requests.RequestException:
            print(f"{white} [{red}!{white}] {red}Internet connection lost. Please check your internet connection.{reset}")
            return False

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)

    parser = argparse.ArgumentParser(description="TorNet - Automate IP address changes using Tor")
    parser.add_argument('--interval', type=int, default=60, help='Time in seconds between IP changes')
    parser.add_argument('--count', type=int, default=10, help='Number of times to change the IP. If 0, change IP indefinitely')
    parser.add_argument('--ip', action='store_true', help='Display the current IP address and exit')
    parser.add_argument('--auto-fix', action='store_true', help='Automatically fix issues (install/upgrade packages)')
    parser.add_argument('--stop', action='store_true', help='Stop all Tor services and tornet processes and exit')
    parser.add_argument('--version', action='version', version='%(prog)s 2.0.0')
    args = parser.parse_args()

    if args.ip:
        ip = ma_ip()
        if ip:
            print_ip(ip)
        return

    if not is_tor_installed():
        print(f"{white} [{red}!{white}] {red}Tor is not installed. Please install Tor and try again.{reset}")
        return

    if args.auto_fix:
        auto_fix()
        print(f"{white} [{green}+{white}]{green} Auto-fix complete.{reset}")
        return

    if args.stop:
        stop_services()
        return

    print_banner()
    initialize_environment()
    change_ip_repeatedly(args.interval, args.count)

if __name__ == "__main__":
    check_internet_connection()
    main()
