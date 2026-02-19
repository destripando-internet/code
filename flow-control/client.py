#!/usr/bin/env -S python3 -u
# Copyright: See AUTHORS and COPYING


# With player:
#  ./client.py --stdin --sndbuf 4096 localhost 2000

import sys
import argparse
import socket
import itertools
import atexit
from time import sleep, monotonic

BLOCK = 10000 * b'x'

rotating = itertools.cycle('|/-\\')


def eprint(msg, end='\n'):
    print(msg, file=sys.stderr, flush=True, end=end)


def retry_connect(sock, endpoint, retries=5, delay=0.5):
    for i in range(retries):
        try:
            return sock.connect(endpoint)
        except socket.error:
            sleep(delay)

    raise ConnectionError(f'Failed to connect to {endpoint} after {retries} attempts')


class CA_RateMeter:
    def __init__(self):
        self.rate = 0
        self.start_time = monotonic()
        self.bytes_from_start = 0

    def update(self, chunk_len):
        self.bytes_from_start += chunk_len
        elapsed = monotonic() - self.start_time
        if elapsed <= 0:
            return

        self.rate = self.bytes_from_start / elapsed

    def __str__(self):
        return f'CA:{self.rate / 1000:.1f} kB/s'


class RateTrace:
    def __init__(self):
        self.start = self.last = monotonic()
        self.file = open('client-stats.csv', 'w')
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
    def __init__(self, host, port, sndbuf_kb=None, use_stdin=False):
        self.trace = RateTrace()
        if use_stdin:
            self.sending_method = self.stdin_sending
        else:
            self.sending_method = self.dummy_sending

        self.sock = socket.socket()
        retry_connect(self.sock, (host, port))
        self.set_sndbuf(sndbuf_kb)


    def set_sndbuf(self, size_B):
        if size_B is not None:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, size_B)
        snd_bufer = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        eprint(f'SNDBUF: {snd_bufer:,} bytes')

    def run(self):
        try:
            self.sending_method()

        except (KeyboardInterrupt, socket.error) as e:
            eprint(f"\nShutting down client. {e}")
        finally:
            self.sock.close()

    def dummy_sending(self):
        self.ca = CA_RateMeter()
        while 1:
            self.sock.sendall(BLOCK)
            self.ca.update(len(BLOCK))
            self.trace.update(self.ca.bytes_from_start, self.ca.rate)
            self.show_stats()

    def stdin_sending(self):
        self.ca = CA_RateMeter()
        while 1:
            data = sys.stdin.buffer.read(1024)
            if not data:
                break

            sent = self.sock.send(data)
            self.ca.update(sent)
            self.trace.update(self.ca.bytes_from_start, self.ca.rate)
            self.show_stats()

    def show_stats(self):
        msg = f'sent:{self.ca.bytes_from_start / 1000:,.1f} kB, {self.ca}'
        eprint(f'\r ({next(rotating)}) {msg} {10 * " "}', end='\r')
        sleep(0.001)


def parse_args(argv):
    parser = argparse.ArgumentParser(description='TCP flow test client')
    parser.add_argument('host', help='Server hostname or IP address')
    parser.add_argument('port', type=int, help='Server port')
    parser.add_argument(
        '--sndbuf', type=int, default=None, metavar='B',
        help='Send bufer size in bytes (default: system default)'
    )
    parser.add_argument(
        '--stdin', action='store_true',
        help='Read data from stdin instead of dummy sending',
    )
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    Sender(args.host, args.port, args.sndbuf, args.stdin).run()


if __name__ == '__main__':
    main(sys.argv[1:])
