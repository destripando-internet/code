FROM mcast-router

RUN apt-get update && \
    apt-get install -y ncat iperf socat smcroute && \
    rm -rf /var/lib/apt/lists/*

CMD ["sh", "-c", \
    "ip route del default && \
    exec sleep infinity"]
