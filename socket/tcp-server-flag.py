#!/usr/bin/env python3

import socket
import signal


def int_handler(sig, frame):
    print("\nSIGINT recibido. Cerrando socket y saliendo...")
    sock.close()
    exit(0)


def handle(conn):
    data = bytes()
    while (i := data.find(b'\n')) == -1:
        data += conn.recv(1024)
    line = data[:i]

    print(f"Se ha recibido el mensaje: {line}")
    conn.sendall(f"Enviaste {len(line)} bytes\n".encode())
    conn.close()


sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', 2000))
sock.listen(5)
signal.signal(signal.SIGINT, int_handler)

while True:
    try:
        conn, client = sock.accept()
        handle(conn)
    except OSError:
        break
