#!/usr/bin/env -S python3 -u

import sys
import socket
import time
import itertools
import atexit

BLOCK = 10000 * b'x'

rotating = itertools.cycle('|/-\\')


def log(msg):
    sys.stderr.write(msg)
    sys.stderr.flush()


class RateTrace:
    def __init__(self):
        self.sent = 0
        self.start = self.last = time.time()
        self.file = open('stats.csv', 'w')
        atexit.register(self.file.close)

    def update(self, bytes_sent, rate):
        now = time.time()
        if now - self.last < 0.001:
            return
        elapsed = now - self.start
        self.last = now
        self.file.write(f'{elapsed:.3f},{bytes_sent},{rate:.3f}\n')
        self.file.flush()
        self.sent = bytes_sent


class Sender:
    def __init__(self, host, port):
        self.sock = socket.socket()
        self.sock.connect((host, port))
        snd_buffer = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF) // 1000
        log(f'Sending buffer size: {snd_buffer:,} kB\n')
        self.trace = RateTrace()

    def run(self):
        self.sent = 0
        self.start_time = time.time()

        try:
            self.sending()
        except KeyboardInterrupt:
            self.sock.close()

    def sending(self):
        while 1:
            rate = self.show_stats()
            self.sent += self.sock.send(BLOCK)
            self.trace.update(self.sent, rate)

    def show_stats(self):
        elapsed = time.time() - self.start_time
        rate = self.sent/1000/elapsed
        msg = f'sent:{self.sent//1000:,} kB, '
        msg += f'rate:{rate:,.0f} kB/s'
        log(f'\r ({next(rotating)}) {msg} {10 * " "}\r')
        time.sleep(0.01)
        return rate


if len(sys.argv) != 3:
    print('Usage: client.py <host> <port>')
    sys.exit(1)

host = sys.argv[1]
port = int(sys.argv[2])
Sender(host, port).run()
