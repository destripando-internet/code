#!/usr/bin/python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <port>"

import sys
import time
import socket
import multiprocessing as mp

MAX_PROCS = 10


def start_new_process(func, args):
    for p in mp.active_children()[::-1][MAX_PROCS:]:
        p.join()

    ps = mp.Process(target=func, args=args)
    ps.start()


def upper(msg):
    time.sleep(1)  # simulates a complex job
    return msg.upper()


def handle(sock, msg, client, n):
    print(f"New request: {n} {client}")
    sock.sendto(upper(msg), client)
    sys.exit(0)


def main(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port))

    n = 0
    while 1:
        msg, client = sock.recvfrom(1024)
        start_new_process(handle, (sock, msg, client, n := n + 1))


if len(sys.argv) != 2:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

try:
    main(int(sys.argv[1]))
except KeyboardInterrupt:
    print("shut down")
