#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <host> <port> <n_clients>"

import sys
import asyncio

queries = "twenty tiny tigers take two taxis to town".split()


class UDPClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, index, queries, on_conn_lost):
        self.index = index
        self.queries = queries
        self.transport = None
        self.on_conn_lost = on_conn_lost

    def connection_made(self, transport):
        self.transport = transport
        self.send_next_query()

    def send_next_query(self):
        if self.queries:
            query = self.queries.pop(0)
            self.transport.sendto(query.encode())
        else:
            self.transport.close()
            self.on_conn_lost.set_result(True)

    def datagram_received(self, data, addr):
        print(f"- [{self.index:>3}] Reply: {data.decode()}")
        self.send_next_query()

    def error_received(self, exc):
        print(f"[{self.index:>3}] Client error: {exc}")
        self.on_conn_lost.set_result(False)


async def udp_client(host, port, index):
    loop = asyncio.get_running_loop()
    on_conn_lost = loop.create_future()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPClientProtocol(index, queries.copy(), on_conn_lost),
        remote_addr=(host, port))

    try:
        await on_conn_lost
    finally:
        transport.close()


async def main(host, port, nclients):
    tasks = [udp_client(host, port, i) for i in range(nclients)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    print('- Clients never served: {}'.format(results.count(False)))


if len(sys.argv) != 4:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

try:
    asyncio.run(main(
        host=sys.argv[1],
        port=int(sys.argv[2]),
        nclients=int(sys.argv[3])))
except KeyboardInterrupt:
    pass
