#!/usr/bin/env python3

import argparse
import socket
import ssl
import sys
import threading
import time
from urllib.parse import urlparse
from colorama import Fore, Style, init

# Initialize Colorama
init(autoreset=True)

# =========================
# Helper Functions
# =========================

def verbose_print(msg, level="info"):
    if args.verbose:
        color = {
            "info": Fore.CYAN,
            "success": Fore.GREEN,
            "warn": Fore.YELLOW,
            "error": Fore.RED
        }.get(level, Fore.WHITE)
        print(color + "[*] " + msg + Style.RESET_ALL)

def build_request(host, payload, method="POST", headers=None):
    """Build a basic HTTP request"""
    if headers is None:
        headers = {}

    request_line = f"{method} / HTTP/1.1\r\n"
    default_headers = {
        "Host": host,
        "User-Agent": "SmuggleScanner/1.0",
        "Content-Length": str(len(payload)),
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "keep-alive"
    }
    default_headers.update(headers)

    header_lines = ''.join(f"{k}: {v}\r\n" for k, v in default_headers.items())
    return f"{request_line}{header_lines}\r\n{payload}".encode()

def connect_target(host, port, use_ssl=False):
    """Connect to host"""
    sock = socket.create_connection((host, port))
    if use_ssl:
        context = ssl.create_default_context()
        sock = context.wrap_socket(sock, server_hostname=host)
    return sock

def connect_proxy(proxy_host, proxy_port):
    """Connect to proxy"""
    sock = socket.create_connection((proxy_host, proxy_port))
    return sock

def send_request(host, port, request, use_ssl=False, proxy=None):
    """Send a raw request either direct or via proxy"""
    try:
        if proxy:
            proxy_host, proxy_port = proxy
            verbose_print(f"Connecting to proxy {proxy_host}:{proxy_port}", "info")
            sock = connect_proxy(proxy_host, proxy_port)
        else:
            verbose_print(f"Connecting to target {host}:{port}", "info")
            sock = connect_target(host, port, use_ssl)

        if proxy and use_ssl:
            # For HTTPS via proxy, need to establish CONNECT tunnel first
            connect_request = f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}\r\n\r\n".encode()
            sock.sendall(connect_request)
            response = sock.recv(4096)
            if b"200" not in response:
                print(Fore.RED + "[-] Proxy tunnel failed." + Style.RESET_ALL)
                return
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=host)

        sock.sendall(request)
        response = sock.recv(8192)
        verbose_print(f"Received {len(response)} bytes", "success")
        return response

    except Exception as e:
        print(Fore.RED + f"[-] Error sending request: {e}" + Style.RESET_ALL)
        return None
    finally:
        try:
            sock.close()
        except:
            pass

def smuggle_attempt(url, payload, headers=None):
    """Attempt smuggling"""
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/"
    use_ssl = parsed.scheme == "https"

    request = build_request(host, payload, headers=headers)
    proxy_tuple = None
    if args.proxy:
        proxy_parsed = urlparse(args.proxy)
        proxy_tuple = (proxy_parsed.hostname, proxy_parsed.port)

    verbose_print(f"Sending smuggle payload to {host}:{port}", "info")
    response = send_request(host, port, request, use_ssl, proxy=proxy_tuple)

    if response:
        if b"HTTP/1.1 301" in response or b"HTTP/1.1 302" in response:
            print(Fore.YELLOW + "[!] Redirect detected. Possible reaction to smuggled request." + Style.RESET_ALL)
        elif b"HTTP/1.1 400" in response:
            print(Fore.RED + "[-] 400 Bad Request (may indicate firewall or server error)." + Style.RESET_ALL)
        else:
            print(Fore.GREEN + "[+] Response received!" + Style.RESET_ALL)
        if args.verbose:
            print(response.decode(errors="ignore"))
    else:
        print(Fore.RED + "[-] No response." + Style.RESET_ALL)

# =========================
# Main Execution
# =========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTTP Request Smuggling Tester")

    parser.add_argument("--url", help="Target URL (example: https://example.com)", required=True)
    parser.add_argument("--proxy", help="Proxy to use (example: http://127.0.0.1:8080)")
    parser.add_argument("--payload", help="Single payload string")
    parser.add_argument("--payload-file", help="Payload file to load (one per line)")
    parser.add_argument("--headers", help="Additional headers (key:value,key:value)", default="")
    parser.add_argument("--threads", type=int, default=1, help="Number of threads")
    parser.add_argument("--rate-limit", type=float, default=0.5, help="Delay between requests in seconds")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    custom_headers = {}
    if args.headers:
        for h in args.headers.split(","):
            try:
                k, v = h.split(":")
                custom_headers[k.strip()] = v.strip()
            except ValueError:
                print(Fore.RED + "[-] Header format error. Use key:value,key:value" + Style.RESET_ALL)
                sys.exit(1)

    try:
        payloads = []
        if args.payload_file:
            with open(args.payload_file, "r") as f:
                payloads = [line.strip() for line in f if line.strip()]
        elif args.payload:
            payloads = [args.payload]
        else:
            print(Fore.RED + "[-] No payload provided." + Style.RESET_ALL)
            sys.exit(1)

        def worker(payload):
            smuggle_attempt(args.url, payload, headers=custom_headers)
            time.sleep(args.rate_limit)

        threads = []
        for payload in payloads:
            t = threading.Thread(target=worker, args=(payload,))
            threads.append(t)
            t.start()

            if args.threads <= 1:
                t.join()

        if args.threads > 1:
            for t in threads:
                t.join()

    except KeyboardInterrupt:
        print(Fore.RED + "\n[!] Script terminated by user." + Style.RESET_ALL)
        sys.exit(0)
