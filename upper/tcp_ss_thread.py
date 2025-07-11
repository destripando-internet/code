#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <port>"

import sys
import time
import os
from socketserver import StreamRequestHandler, ThreadingTCPServer


def upper(msg):
    time.sleep(1)  # simulates a complex job
    return msg.upper()


class Handler(StreamRequestHandler):
    def handle(self):
        print(f"Client connected: {self.client_address}")
        while 1:
            data = os.read(self.rfile.fileno(), 32)
            if not data:
                break

            self.wfile.write(upper(data))
        print(f"Client disconnected: {self.client_address}")


class CustomTCPServer(ThreadingTCPServer):
    allow_reuse_address = True


if len(sys.argv) != 2:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

server = CustomTCPServer(('', int(sys.argv[1])),
                                  Handler)
server.serve_forever()
