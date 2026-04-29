.PHONY: setup-bsr setup-autorp

up: build
	docker network prune -f
	docker compose up --remove-orphans -d
	sudo ./rm-bridge-addrs.sh
	sudo ./setup-hosts.sh

down:
	docker compose down

restart: down up

autorp: setup-autorp restart

setup-autorp:
	./setup-autorp.sh

bsr: setup-bsr restart

setup-bsr:
	./setup-bsr.sh

build:
	docker build -t mcast-router router
	docker build -t mcast-node node

clean: down
	-docker rmi mcast-router mcast-node
	-docker network prune -f
