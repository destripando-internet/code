#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING

import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto("hola".encode(), ('127.0.0.1', 12345))
sock.close()
