#!/bin/bash -

for router in r1 r2 r3; do
    cp rip-$router.conf frr-$router.conf
    docker exec $router vtysh -b
done
