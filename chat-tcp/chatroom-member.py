#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING

import sys
import socket
import selectors
SERVER = ('', 12345)
QUIT = b'bye'


class ChatroomMember:
    def __init__(self, peer):
        self.sock = socket.socket()
        self.sock.connect(peer)

    def run(self):
        selector = selectors.DefaultSelector()
        selector.register(sys.stdin, selectors.EVENT_READ, self.sending)
        selector.register(self.sock, selectors.EVENT_READ, self.receiving)

        while 1:
            for key, mask in selector.select():
                if key.data() in [QUIT, '']:
                    return

    def sending(self):
        message = input().encode()
        self.sock.sendall(message)
        return message

    def receiving(self):
        message = self.sock.makefile().readline().strip()
        print(message)
        return message


try:
    ChatroomMember(SERVER).run()
except KeyboardInterrupt:
    print("shut down.")
