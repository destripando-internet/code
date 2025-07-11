#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <host> <port> <n_clients>"

import sys
import asyncio

TIMEOUT = 80
queries = "twenty tiny tigers take two taxis to town".split()


async def upper_client(host, port, index):
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=TIMEOUT)

        for query in queries:
            data = query.encode()
            writer.write(data)
            await writer.drain()
            reply = await asyncio.wait_for(
                reader.read(len(data)), timeout=TIMEOUT)
            print("- [{0:>3}] Reply: {1}".format(index, reply.decode()))

    except asyncio.TimeoutError:
        print(f"[{index:>3}] Client connection timeout")
        return False

    except ConnectionResetError:
        print(f"[{index:>3}] Client connection lost")
        return False

    writer.close()
    await writer.wait_closed()
    return True


async def main(host, port, nclients):
    tasks = [upper_client(host, port, i) for i in range(nclients)]
    results = await asyncio.gather(*tasks)

    print('- Clients never served: {}'.format(
            results.count(False)))


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
