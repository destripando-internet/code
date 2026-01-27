# Python TCP and UDP servers and clients

These examples implement a very simple service called ``upper``. The ``upper`` servers
reply to the client the uppercase version of the text message that it sends.

As they have a teaching objective. I sacrificed error handling (like exceptions) for
readability and size. A right implementation should add those mechanisms.

You should install ``git`` software and download this repository by this way:

    $ git clone https://github.com/destripando-internet/code

Go to directory ``upper``.


https://github.com/destripando-internet/code/blob/master/upper/


## UDP


* [client][udp-client]
* [single process server][udp-server]
* [multiprocess server][udp-fork]                                   | [doc][fork]
* [multiprocess server with multiprocessing.Process][udp-process]   | [doc][multiprocessing]
* [preforking server][udp-prefork]                                  | [doc][multiprocessing]
* [threadpool server][udp-threadpool]                               | [doc][futures]

* [single process server with SocketServer][udp-ss]                 | [doc][socketserver]

### UDP Async

* [async server][udp-async]                            | [doc][asyncio-protocol]
* [stresss client][udp-stress-client]                  | [doc][asyncio-protocol]


[udp-client]:  https://github.com/destripando-internet/code/blob/master/upper/udp_client.py
[udp-server]:  https://github.com/destripando-internet/code/blob/master/upper/udp_server.py
[udp-fork]:    https://github.com/destripando-internet/code/blob/master/upper/udp_fork.py
[udp-process]: https://github.com/destripando-internet/code/blob/master/upper/udp_process.py
[udp-prefork]: https://github.com/destripando-internet/code/blob/master/upper/udp_prefork.py
[udp-ss]:      https://github.com/destripando-internet/code/blob/master/upper/udp_ss.py
[udp-async]:   https://github.com/destripando-internet/code/blob/master/upper/udp_async_protocol.py
[udp-stress-client]: https://github.com/destripando-internet/code/blob/master/upper/udp_stress_client.py
[udp-threadpool]:    https://github.com/destripando-internet/code/blob/master/upper/udp_threadpool.py


## TCP

* [client][tcp-client]
* [iterative server][tcp-server]

* [forking server][tcp-fork]                                       | [doc][fork]
* [forking server with multiprocessing.Process][tcp-process]       | [doc][multiprocessing]
* [preforking server with multiprocessing.Pool][tcp-prefork-pool]  | [doc][multiprocessing]
* [preforking server with multiprocessing.Pool on accept][tcp-prefork-pool-accept]  | [doc][multiprocessing]

* [threaded server][tcp-thread]                                    | [doc][threading]


### TCP SocketServer

* [iterative server][tcp-ss]                     | [doc][socketserver]
* [forking server][tcp-ss-fork]                  | [doc][socketserver]
* [threaded server][tcp-ss-thread]               | [doc][socketserver]


### TCP Async

* [async server with select][tcp-select]                                     | [doc][select]
* [async server with selectors][tcp-selectors]                               | [doc][selectors]

* [async server with asyncio transports and protocols][tcp-asyncio-protocol] | [doc][asyncio-protocol]
* [async server with asyncio streams][tcp-asyncio-streams]                   | [doc][asyncio-stream]

* [client][tcp-client-async]
* [stress client][tcp-stress-client]                                         | [doc][asyncio-stream]



[tcp-client]:              https://github.com/destripando-internet/code/blob/master/upper/tcp_client.py
[tcp-server]:              https://github.com/destripando-internet/code/blob/master/upper/tcp_server.py

[tcp-fork]:                https://github.com/destripando-internet/code/blob/master/upper/tcp_fork.py
[tcp-process]:             https://github.com/destripando-internet/code/blob/master/upper/tcp_process.py
[tcp-prefork-pool]:        https://github.com/destripando-internet/code/blob/master/upper/tcp_prefork_pool.py
[tcp-prefork-pool-accept]: https://github.com/destripando-internet/code/blob/master/upper/tcp_prefork_pool_accept.py

[tcp-thread]:              https://github.com/destripando-internet/code/blob/master/upper/tcp_thread.py

[tcp-ss]:                  https://github.com/destripando-internet/code/blob/master/upper/tcp_ss.py
[tcp-ss-fork]:             https://github.com/destripando-internet/code/blob/master/upper/tcp_ss_fork.py
[tcp-ss-thread]:           https://github.com/destripando-internet/code/blob/master/upper/tcp_ss_thread.py

[tcp-select]:              https://github.com/destripando-internet/code/blob/master/upper/tcp_select.py
[tcp-selectors]:           https://github.com/destripando-internet/code/blob/master/upper/tcp_selectors.py
[tcp-asyncio-protocol]:    https://github.com/destripando-internet/code/blob/master/upper/tcp_async_protocol.py
[tcp-asyncio-streams]:     https://github.com/destripando-internet/code/blob/master/upper/tcp_async_streams.py
[tcp-client-async]:        https://github.com/destripando-internet/code/blob/master/upper/tcp_client_async.py
[tcp-stress-client]:       https://github.com/destripando-internet/code/blob/master/upper/udp_stress_client.py

[fork]:             https://docs.python.org/3/library/os.html#os.fork
[threading]:        https://docs.python.org/3/library/threading.html
[socketserver]:     https://docs.python.org/3/library/socketserver.html
[select]:           https://docs.python.org/3/library/socketserver.html
[selectors]:        https://docs.python.org/3/library/selectors.html
[multiprocessing]:  https://docs.python.org/3/library/multiprocessing.html
[asyncio-protocol]: https://docs.python.org/3/library/asyncio-protocol.html
[asyncio-stream]:   https://docs.python.org/3/library/asyncio-stream.html
[futures]:          https://docs.python.org/3/library/concurrent.futures.html
