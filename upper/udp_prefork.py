#!/usr/bin/python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <port>"

import sys
import time
import socket
from multiprocessing import Pool

MAX_PROCS = 20


def upper(msg):
    time.sleep(1)  # simulates a complex job
    return msg.upper()


def handle(sock, msg, client, n):
    print(f"New request: {n} {client}")
    sock.sendto(upper(msg), client)


def main(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port))

    with Pool(MAX_PROCS) as pool:
        n = 0
        while 1:
            msg, client = sock.recvfrom(1024)
            pool.apply_async(handle, (sock, msg, client, n := n+1))


if len(sys.argv) != 2:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

try:
    main(int(sys.argv[1]))
except KeyboardInterrupt:
    print("shut down")
