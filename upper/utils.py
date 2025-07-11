def show_select_status(socks, ready):
    def socket_peer(sock):
        if sock == socks[0]:
            return "master"

        try:
            return "{}:{}".format(*sock.getpeername())
        except OSError:
            return "?"

    print("open:  {}\nready: {}\n---".format(
        [socket_peer(x) for x in socks],
        [socket_peer(x) for x in ready]))
