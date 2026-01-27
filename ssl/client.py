#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <host> <port>"

import sys
import socket
import ssl


def main(server_host, server_port):
    context = ssl.create_default_context()
    context.load_verify_locations("ca-cert.pem")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_host, server_port))
    secure_sock = context.wrap_socket(sock, server_hostname=server_host)

    while 1:
        data = sys.stdin.readline().strip().encode()
        if not data:
            break

        sent = secure_sock.send(data)

        msg = bytes()
        while len(msg) < sent:
            msg += secure_sock.recv(32)

        print("Reply is '{0}'".format(msg.decode()))

    sock.close()


if len(sys.argv) != 3:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

try:
    main(sys.argv[1], int(sys.argv[2]))
except KeyboardInterrupt:
    print("shut down")
