#!/usr/bin/env -S python3 -u
# Copyright: See AUTHORS and COPYING

import sys
import socket
import itertools
import atexit
from time import sleep, monotonic

BLOCK = 10000 * b'x'

rotating = itertools.cycle('|/-\\')


def log(msg):
    sys.stderr.write(msg)
    sys.stderr.flush()


class RateTrace:
    def __init__(self):
        self.start = self.last = monotonic()
        self.file = open('stats.csv', 'w')
        atexit.register(self.file.close)

    def update(self, bytes_sent, rate):
        now = monotonic()
        elapsed = now - self.start
        if elapsed < 0.01:
            return
        self.last = now
        self.file.write(f'{elapsed:.3f},{bytes_sent},{rate:.3f}\n')
        self.file.flush()


class Sender:
    def __init__(self, host, port):
        self.sock = socket.socket()
        self.sock.connect((host, port))
        snd_buffer = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF) // 1000
        log(f'Sending buffer size: {snd_buffer:,} kB\n')
        self.trace = RateTrace()

    def run(self):
        try:
            self.sending()
        except (KeyboardInterrupt, socket.error) as e:
            print(f"\nShutting down client. {e}")
            self.sock.close()

    def sending(self):
        self.sent = 0
        self.start_time = monotonic()
        while 1:
            self.sock.sendall(BLOCK)
            self.sent += len(BLOCK)
            self.current_rate = self.rate_kBps()
            self.trace.update(self.sent, self.current_rate)
            self.show_stats()

    def rate_kBps(self):
        elapsed = monotonic() - self.start_time
        return self.sent // 1000 / elapsed

    def show_stats(self):
        msg = f'sent:{self.sent / 1000:,} kB, '
        msg += f'rate:{self.current_rate:,.1f} kB/s'
        log(f'\r ({next(rotating)}) {msg} {10 * " "}\r')
        sleep(0.001)


if len(sys.argv) != 3:
    print('Usage: client.py <host> <port>')
    sys.exit(1)

host = sys.argv[1]
port = int(sys.argv[2])
Sender(host, port).run()
