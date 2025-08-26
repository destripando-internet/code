#!/usr/bin/env -S python3 -u

import sys
import socket
import time
import math
import collections


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

        # Eliminar datos fuera de la ventana
        while self.window and (now - self.window[0][0]) > self.window_size:
            self.window.popleft()

    def rate_kBps(self):
        if not self.window:
            return 0

        window_bytes = sum(b for t, b in self.window)
        elapsed = self.window[-1][0] - self.window[0][0]
        return window_bytes / elapsed / 1000 if elapsed > 0 else 0


class Receiver:
    def __init__(self, port):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
        self.sock.bind(('', port))
        self.sock.listen(1)

    def run(self):
        self.child, client = self.sock.accept()
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
            data = self.child.recv(1024)
            if not data:
                break

            self.received += len(data)
            self.ema.update(len(data))
            self.sma.update(len(data))
            self.show_stats()

            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()

    def show_stats(self):
        ema_rate = self.ema.rate_kBps()
        sma_rate = self.sma.rate_kBps()
        msg = f'received: {self.received//1000:,} kB, '
        msg += f'EMA: {ema_rate:,.1f} kB/s, SMA: {sma_rate:,.1f} kB/s'
        log(f'\r {msg} {10 * " "}\r')


if len(sys.argv) != 2:
    print('Usage: server.py <port>')
    sys.exit(1)

port = int(sys.argv[1])
Receiver(port).run()
