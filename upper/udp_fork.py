#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING

import sys
import os
import time
import socket


class ProcessThrottler(object):
    def __init__(self, max_procs=40):
        self.max_procs = max_procs
        self.procs = []

    def collect_children(self):
        # from socketserver module
        while self.procs:
            opts = os.WNOHANG if len(self.procs) < self.max_procs else 0
            pid, status = os.waitpid(0, opts)
            if not pid:
                break

            self.procs.remove(pid)

    def start_new_process(self, func, args):
        self.collect_children()
        pid = os.fork()
        if pid:
            self.procs.append(pid)
        else:
            func(*args)
            sys.exit()


def upper(msg):
    time.sleep(1)  # simulates a complex job
    return msg.upper()


def handle(sock, msg, client, n):
    print(f"New request: {n} {client}")
    sock.sendto(upper(msg), client)


def main(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port))

    throttler = ProcessThrottler()
    n = 0

    while 1:
        msg, client = sock.recvfrom(1024)
        throttler.start_new_process(
            handle, (sock, msg, client, n := n+1))


if len(sys.argv) != 2:
    print("Usage: {0} <port>".format(sys.argv[0]))
    sys.exit(1)

try:
    main(int(sys.argv[1]))
except KeyboardInterrupt:
    print("shut down")
