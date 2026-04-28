
up: build
	touch frr.conf
	docker network prune -f
	docker compose up --remove-orphans -d
	sudo ./rm-bridge-addrs.sh
	sudo ./setup-hosts.sh

down:
	docker compose down

restart: down up

build:
	docker build -t mcast-router router
	docker build -t mcast-node node

clean: down
	-docker rmi mcast-router mcast-node
	-docker network prune -f

pim: restart
