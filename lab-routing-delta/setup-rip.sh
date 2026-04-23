#!/bin/bash -

for router in r1 r2 r3; do
    cp ripd-$router.conf frr-$router.conf
    docker exec $router vtysh -b
done
