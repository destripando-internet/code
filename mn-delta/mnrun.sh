#!/usr/bin/env bash

node="$1"
shift

# pid=$(pgrep -x "mininet:${node}" | head -n1)
pid=$(pgrep -f "mininet:${node}" | head -n1)

if [ -z "$pid" ]; then
    echo "Node not found: $node" >&2
    exit 1
fi

exec mnexec -a "$pid" "$@"
