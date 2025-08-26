#!/usr/bin/env -S python3 -u

import sys
import socket
import time


def log(msg):
    sys.stderr.write(msg)
    sys.stderr.flush()


class Sender:
    def __init__(self, host, port):
        self.sock = socket.socket()
        self.sock.connect((host, port))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)

    def run(self):
        self.sent = 0
        self.start_time = time.time()

        try:
            self.sending()
        except KeyboardInterrupt:
            pass
        finally:
            self.sock.close()

    def sending(self):
        while 1:
            data = sys.stdin.buffer.read(1024)
            if not data:
                break

            self.sent += self.sock.send(data)
            self.show_stats()

    def show_stats(self):
        elapsed = time.time() - self.start_time
        byterate = self.sent / elapsed / 1000
        msg = f'received: {self.sent//1000:,} kB, '
        msg += f'CA rate: {byterate:,.0f} kB/s, {byterate * 8:,.0f} kb/s'
        log(f'\r {msg} {10 * " "}\r')


if len(sys.argv) != 3:
    print('Usage: client.py <host> <port>')
    sys.exit(1)

host = sys.argv[1]
port = int(sys.argv[2])
Sender(host, port).run()
