#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <port>"

import sys
import time
import socket
from multiprocessing import Pool

MAX_PROCS = 10


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


def main(port):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    sock.listen(5)

    with Pool(MAX_PROCS) as pool:
        while 1:
            conn, client = sock.accept()
            pool.apply_async(handle, (conn, client))


if len(sys.argv) != 2:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

try:
    main(int(sys.argv[1]))
except KeyboardInterrupt:
    print("shut down")
