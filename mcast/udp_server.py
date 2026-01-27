#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
# mcast server
"Usage: {0} <port>"

import sys
import struct
import socket

GROUP = '239.0.0.1'


def main(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port))

    group = struct.pack('4sL', socket.inet_aton(GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, group)

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
    print("shut down")

'''
$ ./UDP_server.py 2000
$ ./UDP_client.py 239.0.0.1 2000
'''
