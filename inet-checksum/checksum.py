#!/usr/bin/python3
# Copyright: See AUTHORS and COPYING
"Internet checksum algorithm RFC-1071"


def inet_checksum(data: bytes) -> int:
    total = 0

    for i in range(0, len(data) - 1, 2):
        total += (data[i] << 8) + data[i+1]

    if len(data) % 2 == 1:
        total += data[-1] << 8

    while (total >> 16):
        total = (total & 0xffff) + (total >> 16)

    return ~total & 0xffff
