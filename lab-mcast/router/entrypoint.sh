#!/bin/sh
set -e

relink() { ip link set "$1" down; ip link set "$1" name "$2"; ip link set "$2" up; }

# This script renamea the router interfaces according to the order of their IP addresses, so that they are deterministic. This is necessary because Docker assigns interface names in an unpredictable order.

# Non-loopback interfaces sorted by IP numerically
ifaces=$(ip -o addr show | awk '$2 != "lo" && /inet / {split($4,a,"/"); print a[1], $2}' \
    | sort -t. -k1,1n -k2,2n -k3,3n -k4,4n | awk '{print $2}')

i=0
for iface in $ifaces; do
    relink "$iface" "eth${i}_r"
    i=$((i + 1))
done

i=0
for iface in $ifaces; do
    relink "eth${i}_r" "eth${i}"
    i=$((i + 1))
done

ip route del default 2>/dev/null || true
sysctl -w net.ipv4.ip_forward=1
/usr/lib/frr/frrinit.sh start
sleep infinity
