#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <host> <port>"

import sys
from socket import socket, SOCK_DGRAM


def main(host, port):
    with socket(type=SOCK_DGRAM) as sock:
        server_endpoint = (host, port)

        while 1:
            data = sys.stdin.readline().strip().encode()
            if not data:
                break

            sock.sendto(data, server_endpoint)
            msg, _ = sock.recvfrom(1024)
            print("Reply is '{}'".format(msg.decode()))


if len(sys.argv) != 3:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

try:
    main(sys.argv[1], int(sys.argv[2]))
except KeyboardInterrupt:
    print("shut down")
