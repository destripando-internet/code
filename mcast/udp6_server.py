#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
# IPv6 mcast server
"Usage: {0} <port>"

import sys
import socket
import struct

GROUP = 'ff02::1:f00d'


def main(port):
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.bind(('', port))

    mreq = socket.inet_pton(socket.AF_INET6, GROUP) + struct.pack('@I', 0)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

    while 1:
        msg, client = sock.recvfrom(1024)
        print("New message: '{}' from {}".format(msg.decode(), client))

    sock.close()


if len(sys.argv) != 2:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

try:
    main(int(sys.argv[1]))
except KeyboardInterrupt:
    print("exited")

'''
$ ./UDP6_server.py 2000
$ ./UDP6_client.py ff02::1:f00d 2000
'''
