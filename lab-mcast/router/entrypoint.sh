#!/bin/sh
set -e

find_iface() { ip -o addr show | awk -v ip="$1/" '$0 ~ ip {print $2}' | grep -v lo | head -1; }
relink() { ip link set "$1" down; ip link set "$1" name "$2"; ip link set "$2" up; }

for i in 0 1 2; do
    eval ip=\$ETH${i}_IP
    [ -z "$ip" ] && continue
    iface=$(find_iface "$ip")
    [ -z "$iface" ] && continue
    relink "$iface" "eth${i}_r"
done
for i in 0 1 2; do
    ip link show "eth${i}_r" >/dev/null 2>&1 && relink "eth${i}_r" "eth${i}"
done

ip route del default 2>/dev/null || true
sysctl -w net.ipv4.ip_forward=1
/usr/lib/frr/frrinit.sh start
sleep infinity
