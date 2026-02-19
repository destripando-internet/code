#!/usr/bin/env -S python3 -u
# Copyright: See AUTHORS and COPYING

import sys
import socket
import math
import collections
import atexit
from time import sleep, monotonic


def mprint(msg, end='\n'):
    print(msg, file=sys.stderr, flush=True, end=end)


class CA_RateMeter:
    def __init__(self):
        self.elapsed = 0
        self.bytes_from_start = 0
        self.rate = 0
        self.start_time = monotonic()

    def update(self, chunk_len):
        self.bytes_from_start += chunk_len
        self.elapsed = monotonic() - self.start_time
        if self.elapsed <= 0:
            return

        self.rate = self.bytes_from_start / self.elapsed

    def __str__(self):
        return f'CA:{self.rate / 1000:.1f} kB/s'


class EMA_RateMeter:
    def __init__(self):
        self.rate = 0
        self.tau = 1.0
        self.last = monotonic()

    def _alpha(self, dt):
        return 1.0 - math.exp(-dt / self.tau) if dt > 0 else 1.0

    def update(self, data_len):
        dt = monotonic() - self.last
        alpha = self._alpha(dt)
        self.rate = alpha * data_len / dt + (1 - alpha) * self.rate
        self.last = monotonic()

    def __str__(self):
        return f'EMA:{self.rate / 1000:.1f} kB/s'


class SMA_RateMeter:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.window = collections.deque()

    def update(self, data_len):
        now = monotonic()
        self.window.append((now, data_len))

        # Remove old data outside the window
        while self.window and (now - self.window[0][0]) > self.window_size:
            self.window.popleft()

    @property
    def rate(self):
        if not self.window:
            return 0

        window_bytes = sum(b for t, b in self.window)
        elapsed = self.window[-1][0] - self.window[0][0]
        return window_bytes / elapsed if elapsed > 0 else 0

    def __str__(self):
        return f'SMA:{self.rate // 1000:.1f} kB/s'


class RateTrace:
    def __init__(self):
        self.start = self.last = monotonic()
        self.file = open('stats.csv', 'w')
        atexit.register(self.file.close)

    def update(self, ca, ema, sma):
        now = monotonic()
        elapsed = now - self.start
        self.last = now
        self.file.write(f'{elapsed:.3f},{ca:.3f},{ema:.3f},{sma:.3f}\n')
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
        try:
            self.conn, client = self.sock.accept()
            mprint(f'Client connected: {client}')
            self.receiving()
        except (KeyboardInterrupt, socket.error) as e:
            mprint(f"\nShutting down server. {e}")
        finally:
            self.sock.close()

    def receiving(self):
        self.received = 0
        self.ca = CA_RateMeter()
        self.ema = EMA_RateMeter()
        self.sma = SMA_RateMeter()
        while 1:
            data = self.conn.recv(1024)
            if not data:
                break

            self.received += (chunk_len := len(data))
            self.ca.update(chunk_len)
            self.ema.update(chunk_len)
            self.sma.update(chunk_len)
            self.trace.update(self.ca.rate, self.ema.rate, self.sma.rate)
            self.show_stats()

            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()

    def show_stats(self):
        msg = f'received:{self.received / 1000:,.1f} kB, '
        msg += f'{self.ca}, {self.ema}, {self.sma}'
        mprint(f'\r {msg} {30 * " "}', end='\r')
        sleep(0.001)


if len(sys.argv) != 2:
    print('Usage: server.py <port>')
    sys.exit(1)

port = int(sys.argv[1])
Receiver(port).run()
