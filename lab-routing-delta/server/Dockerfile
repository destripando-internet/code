FROM debian:bookworm

RUN apt-get update && \
    apt-get install -y procps iproute2 iputils-ping traceroute tshark ncat && \
    rm -rf /var/lib/apt/lists/*

CMD ["sh", "-c", \
    "ip route del default && \
    exec sleep infinity"]
