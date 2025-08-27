#!/usr/bin/env -S python3 -u

import sys
import socket
import time
import math
import collections
import atexit


def log(msg):
    sys.stderr.write(msg)
    sys.stderr.flush()


class EMA:
    def __init__(self):
        self.rate = 0
        self.tau = 1.0
        self.last = time.time()

    def _alpha(self, dt):
        return 1.0 - math.exp(-dt / self.tau) if dt > 0 else 1.0

    def update(self, sent_bytes):
        dt = time.time() - self.last
        alpha = self._alpha(dt)
        self.rate = alpha * sent_bytes / dt + (1 - alpha) * self.rate
        self.last = time.time()

    def rate_kBps(self):
        return self.rate / 1000


class SMA:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.window = collections.deque()

    def update(self, sent_bytes):
        now = time.time()
        self.window.append((now, sent_bytes))

        # Remove old data outside the window
        while self.window and (now - self.window[0][0]) > self.window_size:
            self.window.popleft()

    def rate_kBps(self):
        if not self.window:
            return 0

        window_bytes = sum(b for t, b in self.window)
        elapsed = self.window[-1][0] - self.window[0][0]
        return window_bytes / elapsed / 1000 if elapsed > 0 else 0


class RateTrace:
    def __init__(self):
        self.start = self.last = time.time()
        self.file = open('stats.csv', 'w')
        atexit.register(self.file.close)

    def update(self, sma, ema):
        now = time.time()
        if now - self.last < 0.001:
            return
        elapsed = now - self.start
        self.last = now
        self.file.write(f'{elapsed:.3f},{sma:.3f},{ema:.3f}\n')
        self.file.flush()


class Receiver:
    def __init__(self, port):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
        self.sock.bind(('', port))
        self.sock.listen(1)
        self.trace = RateTrace()

    def run(self):
        self.conn, client = self.sock.accept()
        self.start_time = time.time()

        try:
            self.receiving()
        except KeyboardInterrupt:
            pass
        finally:
            self.sock.close()

    def receiving(self):
        self.received = 0
        self.ema = EMA()
        self.sma = SMA()
        while 1:
            data = self.conn.recv(1024)
            if not data:
                break

            self.received += len(data)
            self.ema.update(len(data))
            self.sma.update(len(data))
            self.trace.update(self.sma.rate_kBps(), self.ema.rate_kBps())
            self.show_stats()

            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()

    def show_stats(self):
        sma_rate = self.sma.rate_kBps()
        ema_rate = self.ema.rate_kBps()
        msg = f'received: {self.received//1000:,} kB, '
        msg += f'EMA: {ema_rate:,.1f} kB/s, SMA: {sma_rate:,.1f} kB/s'
        log(f'\r {msg} {30 * " "}\r')


if len(sys.argv) != 2:
    print('Usage: server.py <port>')
    sys.exit(1)

port = int(sys.argv[1])
Receiver(port).run()
