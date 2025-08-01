#!/usr/bin/env python3

import socket

sock = socket.socket()
sock.connect(('127.0.0.1', 2000))

sock.sendall(b'hola\n')
reply = bytes()
while (i := reply.find(b'\n')) == -1:
    reply += sock.recv(1024)
reply = reply[:i]

print(f"El servidor ha respondido: {reply.decode()}")
sock.close()
