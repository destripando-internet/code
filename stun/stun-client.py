#!/usr/bin/env python3
"Usage: python3 client.py [server] [port]"

import socket
import struct
import secrets
import sys

STUN_BINDING_REQUEST = 0x0001
MAGIC_COOKIE = 0x2112A442
XOR_MAPPED_ADDRESS = 0x0020
MAPPED_ADDRESS = 0x0001

def build_binding_request():
    transaction_id = secrets.token_bytes(12)
    # Header: type (2B) + length (2B) + magic cookie (4B) + transaction id (12B)
    header = struct.pack("!HH", STUN_BINDING_REQUEST, 0)
    header += struct.pack("!I", MAGIC_COOKIE) + transaction_id
    return header, transaction_id

def parse_response(data, transaction_id):
    msg_type, msg_len = struct.unpack("!HH", data[0:4])
    cookie = data[4:8]
    txid = data[8:20]
    if txid != transaction_id:
        raise ValueError("Transaction ID mismatch")

    attrs = data[20:20 + msg_len]
    i = 0
    while i < len(attrs):
        attr_type, attr_len = struct.unpack("!HH", attrs[i:i+4])
        value = attrs[i+4:i+4+attr_len]

        if attr_type == XOR_MAPPED_ADDRESS:
            family = value[1]
            xport = struct.unpack("!H", value[2:4])[0] ^ (MAGIC_COOKIE >> 16)
            xaddr_bytes = value[4:8]
            addr_int = struct.unpack("!I", xaddr_bytes)[0] ^ MAGIC_COOKIE
            ip = socket.inet_ntoa(struct.pack("!I", addr_int))
            return ip, xport

        elif attr_type == MAPPED_ADDRESS:
            family = value[1]
            port = struct.unpack("!H", value[2:4])[0]
            ip = socket.inet_ntoa(value[4:8])
            return ip, port

        # padding to multiples of 4
        i += 4 + attr_len + (-attr_len % 4)

    return None, None

def stun_query(server, port, timeout=3):
    request, txid = build_binding_request()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(request, (server, port))
        data, _ = sock.recvfrom(2048)
        return parse_response(data, txid)
    finally:
        sock.close()

if __name__ == "__main__":
    server = sys.argv[1] if len(sys.argv) > 1 else "stun.l.google.com"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 19302

    print(f"Querying {server}:{port} ...")
    ip, mapped_port = stun_query(server, port)
    if ip:
        print(f"Mapped public IP:     {ip}")
        print(f"Mapped port:          {mapped_port}")
        print(f"Local IP:port:        {socket.gethostbyname(socket.gethostname())}")
    else:
        print("No valid response received")
