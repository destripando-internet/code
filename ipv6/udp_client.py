#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <host> <port>"

import sys
import socket

if len(sys.argv) != 3:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

server_endpoint = (sys.argv[1], int(sys.argv[2]))
sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

while 1:
    data = sys.stdin.readline().strip().encode()
    if not data:
        break

    sock.sendto(data, server_endpoint)
    msg, server = sock.recvfrom(1024)
    print("Reply is '{}'".format(msg.decode()))

sock.close()
