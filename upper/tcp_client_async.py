#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING
"Usage: {0} <host> <port>"


import sys
import asyncio


def readline():
    return sys.stdin.readline().strip().encode()


async def main(host, port):
    reader, writer = await asyncio.open_connection(host, port)

    try:
        while True:
            data = await asyncio.get_event_loop().run_in_executor(None, readline)
            if not data:
                break

            writer.write(data)
            await writer.drain()

            msg = b''
            while len(msg) < len(data):
                chunk = await reader.read(32)
                if not chunk:
                    break
                msg += chunk

            print(f"Reply is '{msg.decode()}'")

    except asyncio.CancelledError:
        pass
    finally:
        writer.close()
        await writer.wait_closed()


if len(sys.argv) != 3:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

try:
    asyncio.run(main(sys.argv[1], int(sys.argv[2])))
except KeyboardInterrupt:
    print("shut down")
