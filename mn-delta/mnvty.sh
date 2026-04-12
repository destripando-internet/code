#!/bin/bash
# mnvty — run vtysh for a Mininet FRR router
# Determines --vty_socket from the running daemon's command line.
#
# Usage: mnvty <router-name> [vtysh args...]
#   e.g. mnvty r1 -c "show ip ospf neighbor"
#        mnvty r1          (interactive)

if [ $# -eq 0 ]; then
    echo "Usage: mnvty <router-name> [vtysh args...]" >&2
    exit 1
fi

ROUTER="$1"
shift

VTY_SOCKET=""
for f in /proc/*/cmdline; do
    args=$(tr '\0' '\n' < "$f" 2>/dev/null) || continue
    echo "$args" | grep -q '/frr/' || continue
    socket=$(echo "$args" | grep -A1 '^--vty_socket$' | tail -1)
    [ -z "$socket" ] && continue
    echo "$socket" | grep -qF "$ROUTER" || continue
    VTY_SOCKET="$socket"
    break
done

if [ -z "$VTY_SOCKET" ]; then
    echo "mnvty: no FRR daemon found for router '$ROUTER'" >&2
    exit 1
fi

exec vtysh --vty_socket "$VTY_SOCKET" "$@"
