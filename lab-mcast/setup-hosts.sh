#!/bin/bash

# add route for 10.0/16 for "host"
ip route replace 10.0.0.0/16 via 10.0.0.3
ip route replace 224.0.0.0/4 via 10.0.0.3

# add "node2" default route
docker exec node2 ip route add default via 10.0.5.2
docker exec node2 ip route add 224.0.0.0/4 via 10.0.5.2

# add "node3" default route
docker exec node3 ip route add default via 10.0.3.2
docker exec node3 ip route add 224.0.0.0/4 via 10.0.3.2
