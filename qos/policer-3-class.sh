#!/bin/bash
# QoS lab: 3 classes, the third one behind a policer
#
#   1: (root, htb, default 99)
#    ├── 1:1  (rate 3mbit ceil 3mbit)
#    │    ├── 1:10 (rate 1mbit ceil 2mbit)  <- port 5201, shaper only
#    │    ├── 1:20 (rate 1mbit ceil 2mbit)  <- port 5202, shaper only
#    │    └── 1:30 (rate 1mbit ceil 2mbit)  <- port 5203, POLICER (1.5mbit) + shaper
#    └── 1:99 (rate 100mbit)  <- default traffic (SSH, background), outside
#                                the 3mbit envelope
#
# The three clients start and finish together. The port-5203 client uses
# several parallel TCP streams to exceed the policer rate and force drops.
#
# Usage:
#   ./policer-3-class.sh user@remote_server

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 user@remote_server" >&2
    exit 1
fi
SSH_TARGET="$1"
# Resolve the real hostname/IP via "ssh -G" (the target may be an ~/.ssh/config alias)
REMOTE_HOST="$(ssh -G "$SSH_TARGET" | awk '/^hostname /{print $2}')"

# ==================== CONFIGURATION ====================
IFACE="enp34s0"

PORT_10=5201
PORT_20=5202
PORT_30=5203

POLICER_RATE="1.5mbit"
POLICER_BURST="32k"

# A single TCP stream stays below the policer rate (RTT/window bound);
# parallel streams are needed to force visible drops.
PORT_30_PARALLEL_STREAMS=16

DURATION=16   # iperf3 client duration (seconds)

# ==================== HELPERS ====================

# Class and filter stats are read with "tc -s -b" (batch mode): both
# queries run in a single tc process, milliseconds apart, so policer and
# queue counters are directly comparable.
BATCH_FILE="$(mktemp)"
printf 'qdisc show dev %s\nclass show dev %s\nfilter show dev %s\n' \
    "$IFACE" "$IFACE" "$IFACE" > "$BATCH_FILE"

snapshot() {
    local label="$1"
    echo ""
    echo "=================================================================="
    echo "  SNAPSHOT: $label   (t=${SECONDS}s)"
    echo "=================================================================="
    echo "\$ sudo tc -s qdisc show dev $IFACE"
    echo "\$ sudo tc -s class show dev $IFACE"
    echo "\$ sudo tc -s filter show dev $IFACE"
    sudo tc -s -b "$BATCH_FILE"
}

cleanup() {
    ssh "$SSH_TARGET" "pkill -f 'iperf3 -s -p ${PORT_10}'" 2>/dev/null || true
    ssh "$SSH_TARGET" "pkill -f 'iperf3 -s -p ${PORT_20}'" 2>/dev/null || true
    ssh "$SSH_TARGET" "pkill -f 'iperf3 -s -p ${PORT_30}'" 2>/dev/null || true
    rm -f "$BATCH_FILE"
}
trap cleanup EXIT

# Disable segmentation offloads so the qdisc counters track individual
# packets (with TSO/GSO one skb may carry several TCP segments)
sudo ethtool -K "$IFACE" tso off gso off gro off

# ==================== 1. PIPELINE SETUP ====================

# Passing through fq_codel forces the kernel to fully release the previous
# qdisc/classes, so all stats start from zero.
sudo tc qdisc del dev "$IFACE" root 2>/dev/null || echo "   (no qdisc to delete)"
sudo tc qdisc add dev "$IFACE" root handle 1: fq_codel
sudo tc qdisc del dev "$IFACE" root
sudo tc qdisc add dev "$IFACE" root handle 1: htb default 99
sudo tc class add dev "$IFACE" parent 1: classid 1:99 htb rate 100mbit
sudo tc class add dev "$IFACE" parent 1: classid 1:1 htb rate 3mbit ceil 3mbit
sudo tc class add dev "$IFACE" parent 1:1 classid 1:10 htb rate 1mbit ceil 2mbit
sudo tc class add dev "$IFACE" parent 1:1 classid 1:20 htb rate 1mbit ceil 2mbit
sudo tc class add dev "$IFACE" parent 1:1 classid 1:30 htb rate 1mbit ceil 2mbit
sudo tc filter add dev "$IFACE" protocol ip parent 1: prio 1 flower \
    ip_proto tcp dst_port "$PORT_10" flowid 1:10
sudo tc filter add dev "$IFACE" protocol ip parent 1: prio 2 flower \
    ip_proto tcp dst_port "$PORT_20" flowid 1:20
# Port 5203 -> 1:30, WITH policer (drops whatever exceeds the rate)
sudo tc filter add dev "$IFACE" protocol ip parent 1: prio 3 flower \
    ip_proto tcp dst_port "$PORT_30" \
    action police rate "$POLICER_RATE" burst "$POLICER_BURST" drop \
    flowid 1:30

snapshot "START - fresh pipeline, counters at zero"

# ==================== 2. START REMOTE IPERF3 SERVERS ====================

echo ""
echo ">>> Starting 3 iperf3 servers on $SSH_TARGET (via SSH)..."
ssh -f "$SSH_TARGET" "rm -f /tmp/iperf3_server_${PORT_10}.log; nohup iperf3 -s -p $PORT_10 > /tmp/iperf3_server_${PORT_10}.log 2>&1 &"
ssh -f "$SSH_TARGET" "rm -f /tmp/iperf3_server_${PORT_20}.log; nohup iperf3 -s -p $PORT_20 > /tmp/iperf3_server_${PORT_20}.log 2>&1 &"
ssh -f "$SSH_TARGET" "rm -f /tmp/iperf3_server_${PORT_30}.log; nohup iperf3 -s -p $PORT_30 > /tmp/iperf3_server_${PORT_30}.log 2>&1 &"
sleep 2

# ==================== 3. GENERATE TRAFFIC (3 CLASSES IN PARALLEL) ====================

echo ""
echo ">>> [t=${SECONDS}s] Starting the 3 clients at once"
echo "    - $PORT_10 and $PORT_20: 1 TCP stream each (shaper only)"
echo "    - $PORT_30: $PORT_30_PARALLEL_STREAMS parallel TCP streams (above the $POLICER_RATE policer)"
iperf3 -c "$REMOTE_HOST" -p "$PORT_10" -t "$DURATION" > /tmp/iperf3_client_${PORT_10}.log 2>&1 &
PID_5201=$!
iperf3 -c "$REMOTE_HOST" -p "$PORT_20" -t "$DURATION" > /tmp/iperf3_client_${PORT_20}.log 2>&1 &
PID_5202=$!
iperf3 -c "$REMOTE_HOST" -p "$PORT_30" -P "$PORT_30_PARALLEL_STREAMS" -t "$DURATION" > /tmp/iperf3_client_${PORT_30}.log 2>&1 &
PID_5203=$!

# Mid-run snapshot, with traffic flowing: the only moment showing negative
# tokens and backlog > 0 (instantaneous values; queues drain and buckets
# refill within milliseconds once the clients stop)
sleep $((DURATION / 2))
snapshot "MIDWAY - traffic flowing (t+$((DURATION / 2))s)"

wait "$PID_5201" 2>/dev/null || true
wait "$PID_5202" 2>/dev/null || true
wait "$PID_5203" 2>/dev/null || true

# ==================== 4. FINAL SNAPSHOT ====================

snapshot "FINAL - cumulative totals"

echo ""
echo ">>> Client $PORT_10 (shaper only):"
echo "\$ iperf3 -c $REMOTE_HOST -p $PORT_10 -t $DURATION"
cat /tmp/iperf3_client_${PORT_10}.log
echo ""
echo ">>> Client $PORT_20 (shaper only):"
echo "\$ iperf3 -c $REMOTE_HOST -p $PORT_20 -t $DURATION"
cat /tmp/iperf3_client_${PORT_20}.log
echo ""
echo ">>> Client $PORT_30 (policer + shaper):"
echo "\$ iperf3 -c $REMOTE_HOST -p $PORT_30 -P $PORT_30_PARALLEL_STREAMS -t $DURATION"
cat /tmp/iperf3_client_${PORT_30}.log

echo ""
echo "=================================================================="
echo "How to read the results:"
echo "  - Port $PORT_30 filter: 'dropped' > 0 (policer)."
echo "  - Class 1:30: 'dropped' 0, 'overlimits' > 0 (shaper holds, not drops)."
echo "  - MIDWAY snapshot: negative 'tokens' and backlog > 0 in the 3 classes."
echo "=================================================================="
