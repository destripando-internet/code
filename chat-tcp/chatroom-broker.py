#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING

import socket
import selectors
QUIT = 'bye'


class ChatroomBroker:
    def main(self):
        with socket.socket() as self.master:
            self.master.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.master.bind(('', 12345))
            self.master.listen(5)

            self.members = {}
            self.selector = selectors.DefaultSelector()
            self.selector.register(self.master, selectors.EVENT_READ, self.acceptor)

            while True:
                for key, mask in self.selector.select():
                    key.data(key.fileobj)

    def acceptor(self, sock):
        conn, addr = self.master.accept()
        print("New connection from", addr)
        self.members[conn] = None
        self.selector.register(conn, selectors.EVENT_READ, self.receiver)

    def receiver(self, conn):
        message = conn.recv(1024).decode().strip()
        if message == QUIT or not message:
            print("User '{}' has left the chat.".format(self.members[conn]))
            self.selector.unregister(conn)
            conn.close()
            del self.members[conn]
            return

        if not self.members[conn]:
            self.members[conn] = message
            print("User '{}' has joined the chat.".format(message))
            return

        sender = self.members[conn]
        for member_conn, nick in self.members.items():
            if member_conn == conn:
                continue

            print(nick, '<-', message)
            encoded = "{}: {}\n".format(sender, message).encode()
            member_conn.sendall(encoded)


try:
    ChatroomBroker().main()
except KeyboardInterrupt:
    print("shut down.")
