#!/usr/bin/env python3
"""
STUN client (RFC 5389) with two modes:

  - No arguments (or [server] [port]): simple query, prints the public
    IP:port mapped by a single STUN server.

  - With --nat-type [local_port]: NAT mapping behavior test per RFC 4787.
    Sends Binding Requests from a SINGLE fixed local port to several
    STUN servers and compares the returned external IP:port as a quick
    sanity check. It then runs the definitive RFC 5780 3-test discovery
    (using whichever configured server advertises an alternate address)
    to give a precise verdict: EIM, ADM, or APDM ("symmetric") mapping.

Usage:
    python3 stun.py [server] [port]
    python3 stun.py --nat-type [local_port]
"""

import argparse
import logging
import secrets
import socket
import struct
import sys

STUN_BINDING_REQUEST = 0x0001
MAGIC_COOKIE = 0x2112A442
MAPPED_ADDRESS = 0x0001
CHANGED_ADDRESS = 0x0005  # legacy RFC 3489 alternate address
XOR_MAPPED_ADDRESS = 0x0020
OTHER_ADDRESS = 0x802c  # RFC 5780 alternate address

DEFAULT_SERVER = "stun.l.google.com"
DEFAULT_PORT = 19302
DEFAULT_LOCAL_PORT = 40000

# Public STUN servers used for the NAT mapping test
MAPPING_TEST_SERVERS = [
    ("stun.l.google.com", 19302),
    ("stun.voipbuster.com", 3478),
    ("stunserver2025.stunprotocol.org", 3478),
    ("stun.sipgate.net", 3478),
    ("stun.nextcloud.com", 443),
    ("stun.miwifi.com", 3478),
    ("stun.schlund.de", 3478),
]


def build_binding_request():
    transaction_id = secrets.token_bytes(12)
    header = struct.pack("!HH", STUN_BINDING_REQUEST, 0)
    header += struct.pack("!I", MAGIC_COOKIE) + transaction_id
    return header, transaction_id


def parse_response(data, transaction_id):
    if len(data) < 20:
        return None, None

    msg_type, msg_len = struct.unpack("!HH", data[0:4])
    txid = data[8:20]
    if txid != transaction_id:
        return None, None

    attrs = data[20:20 + msg_len]
    i = 0
    mapped = (None, None)
    while i + 4 <= len(attrs):
        attr_type, attr_len = struct.unpack("!HH", attrs[i:i + 4])
        value = attrs[i + 4:i + 4 + attr_len]

        if attr_type == XOR_MAPPED_ADDRESS and len(value) >= 8:
            xport = struct.unpack("!H", value[2:4])[0] ^ (MAGIC_COOKIE >> 16)
            addr_int = struct.unpack("!I", value[4:8])[0] ^ MAGIC_COOKIE
            ip = socket.inet_ntoa(struct.pack("!I", addr_int))
            return ip, xport  # XOR-MAPPED-ADDRESS takes priority (RFC 5389)

        elif attr_type == MAPPED_ADDRESS and len(value) >= 8:
            port = struct.unpack("!H", value[2:4])[0]
            ip = socket.inet_ntoa(value[4:8])
            mapped = (ip, port)

        i += 4 + attr_len + (-attr_len % 4)  # padding to a multiple of 4

    return mapped


def parse_alt_address(data):
    "Extract the alternate IP:port (OTHER-ADDRESS / legacy CHANGED-ADDRESS) a server advertises."
    if len(data) < 20:
        return None

    msg_len = struct.unpack("!H", data[2:4])[0]
    attrs = data[20:20 + msg_len]
    i = 0
    while i + 4 <= len(attrs):
        attr_type, attr_len = struct.unpack("!HH", attrs[i:i + 4])
        value = attrs[i + 4:i + 4 + attr_len]

        if attr_type in (OTHER_ADDRESS, CHANGED_ADDRESS) and len(value) >= 8:
            port = struct.unpack("!H", value[2:4])[0]
            ip = socket.inet_ntoa(value[4:8])
            return ip, port

        i += 4 + attr_len + (-attr_len % 4)

    return None


def send_binding_request(server, port, local_port=0, timeout=3):
    request, txid = build_binding_request()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", local_port))
    sock.settimeout(timeout)
    try:
        sock.sendto(request, (server, port))
        data, _ = sock.recvfrom(2048)
        return data, txid
    except socket.timeout:
        return None, txid
    finally:
        sock.close()


def stun_query(server, port, local_port=0, timeout=3):
    data, txid = send_binding_request(server, port, local_port, timeout)
    if data is None:
        return None, None
    return parse_response(data, txid)


def run_query(server, port):
    logging.info(f"Querying {server}:{port}:")
    try:
        ip, mapped_port = stun_query(server, port)
    except socket.gaierror as e:
        logging.info(f"- {e}. No response (timeout or error)")
        print("No valid response received")
        return
    if ip:
        logging.info(f"- External endpoint: {ip}:{mapped_port}")
        print(f"Mapped public IP:     {ip}")
        print(f"Mapped port:          {mapped_port}")
        print(f"Local IP:port:        {socket.gethostbyname(socket.gethostname())}")
    else:
        print("No valid response received")


def run_mapping_behavior_test(local_port, discovery):
    "RFC 5780 3-test NAT mapping behavior discovery (EIM/ADM/APDM) using one compliant server."
    host, port, ma1, alt_ip, alt_port = discovery
    logging.info(f"Discovery server: {host}:{port} (alt-address {alt_ip}:{alt_port})")
    logging.info(f"Test I  ({host}:{port}) -> {ma1[0]}:{ma1[1]}")

    data2, txid2 = send_binding_request(alt_ip, port, local_port=local_port)
    if data2 is None:
        return "inconclusive (no response for Test II)"
    ma2 = parse_response(data2, txid2)
    logging.info(f"Test II ({alt_ip}:{port}) -> {ma2[0]}:{ma2[1]}")

    if ma1 == ma2:
        return "EIM (Endpoint-Independent Mapping)"

    data3, txid3 = send_binding_request(alt_ip, alt_port, local_port=local_port)
    if data3 is None:
        return "inconclusive (no response for Test III)"
    ma3 = parse_response(data3, txid3)
    logging.info(f"Test III ({alt_ip}:{alt_port}) -> {ma3[0]}:{ma3[1]}")

    if ma2 == ma3:
        return "ADM (Address-Dependent Mapping) / Symmetric NAT"
    return "APDM (Address and Port-Dependent Mapping) / Symmetric NAT"


def run_nat_type_test(local_port):
    logging.info(f"Fixed local port: {local_port}")

    results = []
    discovery = None
    for host, port in MAPPING_TEST_SERVERS:
        logging.info(f"Querying {host}:{port}:")
        try:
            data, txid = send_binding_request(host, port, local_port=local_port)
        except socket.gaierror as e:
            logging.info(f"- {e}. No response (timeout or error)")
            continue
        if data is None:
            logging.info("- No response (timeout or error)")
            continue

        ip, ext_port = parse_response(data, txid)
        if not ip:
            logging.info("- No response (timeout or error)")
            continue

        logging.info(f"- External endpoint: {ip}:{ext_port}")
        results.append((host, ip, ext_port))

        if discovery is None:
            alt = parse_alt_address(data)
            if alt:
                discovery = (host, port, (ip, ext_port), alt[0], alt[1])

    if len(results) < 2:
        print("Not enough responses to compare. Try another local port")
        print("or check that the firewall isn't blocking inbound UDP replies.")
        return

    ports = sorted({ext_port for _, _, ext_port in results})
    ips = sorted({ip for _, ip, _ in results})

    print(f"Public IPs: [{', '.join(ips)}]")
    print(f"External ports seen: {ports}")
    print()

    if discovery is None:
        print("No configured server advertises an alternate address (RFC 5780);")
        print("cannot run the definitive mapping test. Run with --check-servers")
        print("to see which configured servers support it.")
        return

    verdict = run_mapping_behavior_test(local_port, discovery)
    print(f"Mapping behavior: {verdict}")



def run_check_servers():
    print(f"Checking {len(MAPPING_TEST_SERVERS)} configured server(s)...\n")
    for host, port in MAPPING_TEST_SERVERS:
        try:
            data, txid = send_binding_request(host, port)
        except socket.gaierror as e:
            print(f"{host}:{port} -> DNS FAIL: {e}")
            continue
        if data is None:
            print(f"{host}:{port} -> TIMEOUT / no response")
            continue

        ip, mapped_port = parse_response(data, txid)
        alt = parse_alt_address(data)
        alt_str = f"{alt[0]}:{alt[1]}" if alt else "none"
        print(f"{host}:{port} -> OK  mapped={ip}:{mapped_port}  alt-address={alt_str}")


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("server", nargs="?", default=DEFAULT_SERVER,
                         help=f"STUN server to query (default: {DEFAULT_SERVER})")
    parser.add_argument("port", nargs="?", type=int, default=DEFAULT_PORT,
                         help=f"STUN server port (default: {DEFAULT_PORT})")
    parser.add_argument("--nat-type", nargs="?", type=int, const=DEFAULT_LOCAL_PORT,
                         metavar="LOCAL_PORT", dest="nat_type_local_port",
                         help="Run the NAT mapping behavior test and give a definitive "
                              "EIM/ADM/APDM verdict (RFC 5780) instead of a simple query. "
                              f"Optional fixed local port (default: {DEFAULT_LOCAL_PORT})")
    parser.add_argument("--check-servers", action="store_true",
                         help="Check connectivity of the configured mapping-test "
                              "servers (and whether they advertise an alternate "
                              "address per RFC 5780) and exit")
    parser.add_argument("-v", "--verbose", action="store_true",
                         help="Show per-query progress messages")
    return parser.parse_args(argv)


def main():
    args = parse_args(sys.argv[1:])
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
    )
    if args.check_servers:
        run_check_servers()
    elif args.nat_type_local_port is not None:
        run_nat_type_test(args.nat_type_local_port)
    else:
        run_query(args.server, args.port)


if __name__ == "__main__":
    main()
