FROM debian:12-slim

RUN apt-get update && \
    apt-get install -y dnsmasq iproute2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 53/udp 53/tcp

# Ejecutar dnsmasq en primer plano (-k)
# --log-facility=- envía los logs a stdout para verlos con docker logs
# --log-dhcp documenta la actividad DHCP
CMD ["dnsmasq", "-k", "--log-facility=-", "--log-dhcp"]
