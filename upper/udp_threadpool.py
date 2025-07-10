#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <port>"

import sys
import time
from threading import Thread, current_thread
import queue
from socket import socket, SOCK_DGRAM
from concurrent.futures import ThreadPoolExecutor

MAX_THREADS = 20
output_queue = queue.Queue()


def upper(msg):
    time.sleep(1)  # Simulate heavy processing
    return msg.upper()


def handle(msg, client, n):
    print(f"Processing request {n} from {client}, thread {current_thread().name}")
    response = upper(msg)
    output_queue.put((response, client))


def responder(sock):
    while True:
        response, client = output_queue.get()
        sock.sendto(response, client)


def main(port):
    sock = socket(type=SOCK_DGRAM)
    sock.bind(('', port))

    Thread(target=responder, args=(sock,), daemon=True).start()

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        n = 0
        while True:
            msg, client = sock.recvfrom(1024)
            executor.submit(handle, msg, client, n := n+1)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__.format(sys.argv[0]))
        sys.exit(1)

    try:
        main(int(sys.argv[1]))
    except KeyboardInterrupt:
        print("shut down")
