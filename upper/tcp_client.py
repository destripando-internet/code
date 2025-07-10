#!/usr/bin/python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <host> <port>"

import sys
from socket import socket


def main(host, port):
    with socket() as sock:
        sock.connect((host, port))

        while 1:
            data = sys.stdin.readline().strip().encode()
            if not data:
                break

            sock.sendall(data)

            msg = bytes()
            while len(msg) < len(data):
                msg += sock.recv(32)

            print("Reply is '{0}'".format(msg.decode()))


if len(sys.argv) != 3:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

try:
    main(sys.argv[1], int(sys.argv[2]))
except KeyboardInterrupt:
    print("shut down")
