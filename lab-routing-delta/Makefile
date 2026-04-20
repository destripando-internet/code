
up: build
	touch frr-r1.conf frr-r2.conf frr-r3.conf
	docker compose up --remove-orphans -d
	sudo ./rm-bridge-addrs.sh
	sudo ./setup-hosts.sh

down:
	docker compose down

restart: down build up

build:
	docker build -t lab-delta-router router
	docker build -t lab-delta-server server

clean: down
	-docker rmi lab-delta-router lab-delta-server
	-docker network prune -f

static: restart
	./setup-static.sh

.PHONY: rip
rip: restart
	./setup-rip.sh

ospf: restart
	./setup-ospf.sh

eigrp: restart
	./setup-eigrp.sh
