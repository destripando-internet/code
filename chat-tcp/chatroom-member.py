#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING

import sys
import socket
import selectors

QUIT = b'bye'

class ChatroomMember:
    def __init__(self, broker, nick):
        self.sock = socket.socket()
        self.sock.connect(broker)
        self.nick = nick

    def run(self):
        self.sock.sendall(self.nick.encode())

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


if len(sys.argv) != 3:
    exit("Usage: ./chatroom-member.py <broker_address> <nick>")

broker = (sys.argv[1], 12345)

try:
    ChatroomMember(broker, nick=sys.argv[2]).run()
except (KeyboardInterrupt, EOFError):
    print("shut down.")
