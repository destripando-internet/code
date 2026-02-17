#!/usr/bin/env -S python3 -u
# Copyright: See AUTHORS and COPYING

import sys
import socket
from time import sleep, monotonic


def log(msg):
    sys.stderr.write(msg)
    sys.stderr.flush()


class Receiver:
    def __init__(self, port, target_rate_kBps):
        self.target_rate = target_rate_kBps * 1000
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', port))
        self.sock.listen(1)

    def run(self):
        self.conn, client = self.sock.accept()
        print(f'Client connected: {client}')

        rcv_buffer = self.conn.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF) // 1000
        log(f'Receiving buffer size: {rcv_buffer:,} kB\n')

        try:
            self.receiving()
        except KeyboardInterrupt:
            self.sock.close()

    def receiving(self):
        self.received = 0
        self.start_time = monotonic()
        while 1:
            data = self.conn.recv(4096)
            if not data:
                break

            self.received += len(data)
            elapsed = monotonic() - self.start_time
            self.current_rate = self.received / elapsed
            self.show_stats()

            if self.current_rate <= self.target_rate:
                continue

            adjust_time = (self.received / self.target_rate) - elapsed
            if adjust_time > 0:
                sleep(adjust_time)

    def show_stats(self):
        msg = f'received:{self.received // 1000:,} kB, '
        msg += f'rate:{self.current_rate / 1000:,.1f} kB/s'
        log(f'\r {msg} {10 * " "}\r')
        sleep(0.001)


if len(sys.argv) != 3:
    print('Usage: server.py <port> <rx_limit_kBps>')
    sys.exit(1)

port = int(sys.argv[1])
rate_limit = int(sys.argv[2])
Receiver(port, rate_limit).run()
