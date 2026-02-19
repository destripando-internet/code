#!/usr/bin/env -S python3 -u
# Copyright: See AUTHORS and COPYING

import atexit
import sys
import socket
import argparse
import collections
from time import sleep, monotonic
import math


def eprint(msg, end='\n'):
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
        self.file = open('server-stats.csv', 'w')
        atexit.register(self.file.close)

    def update(self, ca, ema, sma):
        now = monotonic()
        elapsed = now - self.start
        self.last = now
        self.file.write(f'{elapsed:.3f},{ca:.3f},{ema:.3f},{sma:.3f}\n')
        self.file.flush()


class Receiver:
    def __init__(self, args):
        self.target_rate = args.limit * 1000 if args.limit > 0 else None
        self.rcvbuf_B = args.rcvbuf
        self.step_size = args.step
        self.use_stdout = args.stdout
        self.show_ema = args.ema
        self.show_sma = args.sma
        if args.step:
            self.receiving_method = self.step_receiving
        else:
            self.receiving_method = self.limited_receiving

        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', args.port))
        self.sock.listen(1)
        self.trace = RateTrace()

    def run(self):
        try:
            self.conn, client = self.sock.accept()
            eprint(f'Client connected: {client}')
            self.set_rcvbuf(self.rcvbuf_B)
            self.receiving_method()

        except KeyboardInterrupt:
            eprint('\nShutting down server...')
        finally:
            self.sock.close()

    def set_rcvbuf(self, size_B):
        if size_B is not None:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, size_B)
        rcv_bufer = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        eprint(f'RCVBUF: {rcv_bufer:,} bytes')

    def limited_receiving(self):
        self.ca = CA_RateMeter()
        self.ema = EMA_RateMeter()
        self.sma = SMA_RateMeter()
        while 1:
            data = self.conn.recv(4096)
            if not data:
                break

            chunk_len = len(data)
            self.ca.update(chunk_len)
            self.ema.update(chunk_len)
            self.sma.update(chunk_len)
            self.trace.update(self.ca.rate, self.ema.rate, self.sma.rate)
            self.show_stats()

            if self.use_stdout:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

            if self.target_rate is None or self.ca.rate <= self.target_rate:
                continue

            adjust_time = (self.ca.bytes_from_start / self.target_rate) - self.ca.elapsed
            if adjust_time > 0:
                sleep(adjust_time)

    def step_receiving(self):
        input('Press ENTER to receive > ')
        received = 0
        while 1:
            count = 0
            pending = self.step_size * 1000
            while count < pending:
                data = self.conn.recv(min(4096, pending - count))
                if not data:
                    return
                count += len(data)
            received += count

            input(f'received: {received//1000:,} kB > ')

    def show_stats(self):
        msg = f'received:{self.ca.bytes_from_start / 1000:,.1f} kB, '
        msg += f'{self.ca}'
        if self.show_ema:
            msg += f', {self.ema}'
        if self.show_sma:
            msg += f', {self.sma}'
        eprint(f'\r {msg} {10 * " "}', end='\r')
        sleep(0.001)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Flow control server with optional limitid receiving rate')
    parser.add_argument('port', type=int, help='Port to listen on')
    parser.add_argument(
        '--limit', type=int, default=0,
        help='limit max receive rate in kB/s (default: 0=no limit)'
    )
    parser.add_argument(
        '--step', type=int, default=None,
        help='Use step-by-step blocks (kB). Requires manual signaling.'
    )
    parser.add_argument(
        '--rcvbuf', type=int, default=None, metavar='B',
        help='Set receive buffer size bytes (default: system default)')
    parser.add_argument(
        '--stdout', action='store_true',  help='Print data to stdout')
    parser.add_argument(
        '--ema', action='store_true', help='Show EMA rate')
    parser.add_argument(
        '--sma', action='store_true', help='Show SMA rate')

    args = parser.parse_args()
    Receiver(args).run()
