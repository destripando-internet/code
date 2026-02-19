#!/usr/bin/env -S python3 -u
# Copyright: See AUTHORS and COPYING

import sys
import socket
import argparse
from time import sleep, monotonic


def log(msg, end='\n'):
    print(msg, file=sys.stderr, flush=True, end=end)


class Receiver:
    def __init__(self, port, target_rate_kBps, step_size_kB):
        self.target_rate = target_rate_kBps * 1000 if target_rate_kBps > 0 else None
        self.step_size = step_size_kB
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', port))
        self.sock.listen(1)

        if step_size_kB != 0:
            self.receiving_method = self.step_receiving
        else:
            self.receiving_method = self.limited_receiving

    def run(self):
        try:
            self.conn, client = self.sock.accept()
            print(f'Client connected: {client}')

            rcv_buffer = self.conn.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF) // 1000
            log(f'Receiving buffer size: {rcv_buffer:,} kB')

            self.receiving_method()

        except KeyboardInterrupt:
            print('\nShutting down server...')
            self.sock.close()

    def limited_receiving(self):
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

            if self.target_rate is None or self.current_rate <= self.target_rate:
                continue

            adjust_time = (self.received / self.target_rate) - elapsed
            if adjust_time > 0:
                sleep(adjust_time)

    def step_receiving(self):
        input('Press ENTER to receive > ')
        received = 0
        while 1:
            step_received = 0
            pending = self.step_size * 1000
            while step_received < pending:
                data = self.conn.recv(min(4096, pending - step_received))
                if not data:
                    return
                step_received += len(data)
            received += step_received

            input(f'received: {received//1000:,} kB > ')

    def show_stats(self):
        msg = f'received:{self.received // 1000:,} kB, '
        msg += f'rate:{self.current_rate / 1000:,.1f} kB/s'
        log(f'\r {msg} {10 * " "}', end='\r')
        sleep(0.001)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Flow control server with optional limitid receiving rate'
    )
    parser.add_argument('port', type=int, help='Port to listen on')
    parser.add_argument(
        '--limit', type=int, default=0,
        help='Maximum receive rate in kB/s (0 for no limit, default: 0)'
    )
    parser.add_argument(
        '--step', type=int, default=None,
        help='Use step-by-step receiving mode with specified kB per step (requires manual input)'
    )

    args = parser.parse_args()
    Receiver(args.port, args.limit, args.step).run()
