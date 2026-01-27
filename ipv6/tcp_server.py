#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <host> <port>"

import sys
import time
import socket


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


def main(host, port):
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(5)

    while 1:
        conn, client = sock.accept()
        handle(conn, client)


if len(sys.argv) != 3:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

try:
    main(sys.argv[1], int(sys.argv[2]))
except KeyboardInterrupt:
    print("exited")


'''
$ ./server.py "::1" 2000
$ ncat -6 ::1 2000

--
$ ./server.py "" 2000
$ echo hello | ncat -6 ::1 2000
--
$ echo hello | ncat -4 127.0.0.1 2000
'''
