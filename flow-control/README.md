Playing with TCP flow control
-----------------------------

- `server.py` is a receiver limiting input rate.
- `client.py` sends as fast as possible.
- `lazy-server.py` waits for the user to press a key before receiving some data, then pauses again.

You may observe that the client stops sending when the buffers are full and resumes once there is free space.

Run this command to view socket variables:

    $ ss -timon sport = 2000 or dport = 2000
