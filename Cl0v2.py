import socket
import ssl
import sys
import argparse

def read_file(path):
    with open(path, 'rb') as f:
        return f.read()

def send_dual_requests(host, port, req1, req2, use_ssl=False):
    s = socket.create_connection((host, port))
    if use_ssl:
        context = ssl.create_default_context()
        s = context.wrap_socket(s, server_hostname=host)

    s.sendall(req1)
    s.sendall(req2)

    response = b""
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
    except:
        pass
    finally:
        s.close()

    print(response.decode(errors='replace'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Send two raw HTTP requests over a single connection (e.g. for request smuggling testing)."
    )
    parser.add_argument("host", help="Target host (e.g. example.com)")
    parser.add_argument("port", type=int, help="Target port (e.g. 80 or 443)")
    parser.add_argument("request1", help="Path to first request file")
    parser.add_argument("request2", help="Path to second request file")
    parser.add_argument("--ssl", action="store_true", help="Use SSL/TLS (for port 443)")

    args = parser.parse_args()

    req1 = read_file(args.request1)
    req2 = read_file(args.request2)

    send_dual_requests(args.host, args.port, req1, req2, args.ssl)
