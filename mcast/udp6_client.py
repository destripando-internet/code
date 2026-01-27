#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
# IPv6 mcast client
"Usage: {0} <group> <port>"

import sys
import socket


def main(group, port):
    server_endpoint = (group, port)
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    while 1:
        print(end="> ")
        data = sys.stdin.readline().strip().encode()
        if not data:
            break

        sock.sendto(data, server_endpoint)

    sock.close()


if len(sys.argv) != 3:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)


try:
    main(sys.argv[1], int(sys.argv[2]))
except KeyboardInterrupt:
    print("exited")
