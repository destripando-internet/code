#!/bin/bash

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root. Try with sudo."
    exit 1
fi

flush_ips() {
    local dev=$1
    echo $dev

    if ! ip link show dev $dev &>/dev/null; then
        echo "  skipping $dev (device not found)"
        return
    fi

    ip link set dev $dev down
    ip addr flush dev $dev
    ip -6 addr flush dev $dev
    ip link set dev $dev up
}

echo Removing bridge addresses...

project=$(basename $(pwd))
for net_id in $(docker network ls --filter "driver=bridge" | grep "$project" | grep -v "_N0" | awk '{print $1}'); do
    bridge=$(docker network inspect "$net_id" --format '{{index .Options "com.docker.network.bridge.name"}}')
    [ -z "$bridge" ] && bridge="br-$net_id"
    flush_ips "$bridge"
done
