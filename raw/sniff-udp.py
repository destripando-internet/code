#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING

import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                     socket.getprotobyname('udp'))
while 1:
    print("--\n{!r}".format(sock.recv(1600)))
