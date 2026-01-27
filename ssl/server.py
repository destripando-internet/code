#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
#
# Generate SSL certificates with: make generate-certs
# $ openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes


"Usage: {0} <port>"

import sys
import time
import socket
import ssl
import signal


def upper(msg):
    time.sleep(1)  # simulates a complex job
    return msg.upper()


def handle(sock, client):
    print(f"Client connected: {client}")
    while 1:
        data = sock.recv(32)
        if not data:
            break

        sock.sendall(upper(data))

    sock.close()
    print(f"Client disconnected: {client}")


if len(sys.argv) != 2:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)


signal.signal(signal.SIGINT, lambda n, f: sys.exit(0))
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', int(sys.argv[1])))
sock.listen(5)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile='server-cert.pem', keyfile='server-key.pem')

while 1:
    conn, client = sock.accept()

    try:
        with context.wrap_socket(conn, server_side=True) as secure_conn:
            handle(secure_conn, client)

    except ssl.SSLError as e:
        print(f"SSL error: {e}")
        conn.close()
