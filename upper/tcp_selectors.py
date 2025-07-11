#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <port>"

import sys
import socket
import time
import selectors


def upper(msg):
    time.sleep(1)  # simulates a complex job
    return msg.upper()


class Server:
    def __init__(self, port):
        self.master = socket.socket()
        self.master.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.master.bind(('', port))
        self.master.listen(5)
        self.socks = [self.master]

    def master_handler(self, sock):
        conn, client = sock.accept()
        self.selector.register(conn, selectors.EVENT_READ, self.child_handler)
        print(f"- Client connected: {client}")

    def child_handler(self, conn):
        data = conn.recv(32)
        if not data:
            self.selector.unregister(conn)
            conn.close()
            return

        conn.sendall(upper(data))

    def run(self):
        self.selector = selectors.DefaultSelector()
        self.selector.register(
            self.master, selectors.EVENT_READ, self.master_handler)

        while 1:
            for key, mask in self.selector.select():
                key.data(key.fileobj)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__.format(sys.argv[0]))
        exit(1)

    try:
        server = Server(int(sys.argv[1]))
        server.run()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
        exit(0)
