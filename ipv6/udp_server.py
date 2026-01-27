#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <host> <port>"

import sys
import time
import socket


def upper(msg):
    time.sleep(1)  # simulates a complex job
    return msg.upper()


def handle(sock, msg, client, n):
    print(f"New request {n} {client}")
    sock.sendto(upper(msg), client)


def main(host, port):
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.bind((host, port))

    n = 0
    while 1:
        msg, client = sock.recvfrom(1024)
        handle(sock, msg, client, n := n+1)


if len(sys.argv) != 3:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

try:
    main(sys.argv[1], int(sys.argv[2]))
except KeyboardInterrupt:
    print("exited")


'''
$ ./server.py "::1" 2000
$ ncat -u -6 ::1 2000

--
$ ./server.py "" 2000
$ ncat -u -6 ::1 2000
--
$ ncat -u -4 127.0.0.1 2000
'''
