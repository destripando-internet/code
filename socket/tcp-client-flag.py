#!/usr/bin/env python3

import socket


def readline(conn):
    data = bytes()
    while (i := data.find(b'\n')) == -1:
        chunk = conn.recv(1024)
        if not chunk:
            return data
        data += chunk
    line = data[:i]
    return line


sock = socket.socket()
sock.connect(('127.0.0.1', 2000))

sock.sendall(b'hola\n')
reply = readline(sock)

print(f"El servidor ha respondido: {reply.decode()}")
sock.close()
