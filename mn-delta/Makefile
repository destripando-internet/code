
up:
	sudo python3 topology.py

down:
	sudo mn -c

static:
	sudo python3 topology.py --static

.PHONY: rip
rip:
	sudo python3 topology.py --rip

ospf:
	sudo python3 topology.py --ospf

eigrp:
	sudo python3 topology.py --eigrp

clean:
	sudo mn -c
	sudo find /var/run/netns -maxdepth 1 -type l \( -name r1 -o -name r2 -o -name r3 -o -name server \) -delete

test: clean
	sudo python3 -m unittest -v test_topology

.PHONY: test clean
