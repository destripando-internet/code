FROM debian:bookworm

RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl -s https://deb.frrouting.org/frr/keys.gpg | tee /usr/share/keyrings/frrouting.gpg > /dev/null && \
    echo "deb [signed-by=/usr/share/keyrings/frrouting.gpg] https://deb.frrouting.org/frr bookworm frr-10" \
        > /etc/apt/sources.list.d/frr.list && \
    apt-get update && \
    apt-get install -y procps iproute2 iputils-ping traceroute tshark frr && \
    rm -rf /var/lib/apt/lists/*

CMD ["sh", "-c", \
    "ip route del default && \
    sysctl -w net.ipv4.ip_forward=1 && \
    /usr/lib/frr/frrinit.sh start && \
    sleep infinity"]
