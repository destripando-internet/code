# Demo WireGuard con Docker

Demo de un servidor y cliente WireGuard ejecutándose en contenedores Docker, ambos con la imagen oficial `linuxserver/wireguard`.

## Arquitectura

```
  host
  └─ docker network (bridge)
       ├─ vpn-server
       │    wg0: 10.13.13.1
       │    puerto UDP 51820 expuesto al host
       └─ vpn-client
            wg0: 10.13.13.2  (peer1, asignada por el servidor)
```

La subred de la VPN es `10.13.13.0/24`. El servidor genera automáticamente la onfiguración para dos peers:

- **peer1** — usado por el contenedor cliente.
- **peer2** — disponible para conectar el propio host como cliente VPN.


## Estructura de ficheros relevantes

```
wireguard/
├── compose.yml           # Especificación "docker compose"
├── Makefile              # Reglas de puesta en marcha
├── server/               # GENERADO al arrancar el servidor
│   ├── peer1/
│   │   └── peer1.conf    # Configuración del peer1 (cliente docker)
│   └── peer2/
│       └── peer2.conf    # Configuración del peer2 (cliente host)
└── client/               # GENERADO por 'make client-setup'
    └── peer1.conf        # Copia del perfil peer1 para el contenedor cliente
```


## Puesta en marcha desde cero

### 1. Arrancar el servidor

    $ make server-setup
    ✔ Image linuxserver/wireguard Pulled                                                                                                   5.7s
    ✔ Network wireguard_default   Created                                                                                                  0.0s
    ✔ Container vpn-server        Started

Esto ejecuta `docker compose up -d server`. Genera automáticamente las claves del servidor y los perfiles de los peers configurados (`PEERS=2`) en el directorio `server/`.

Comprueba que el servidor está activo y tiene su interfaz `wg0`:

    $ docker compose exec server ip a show dev wg0
    4: wg0: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1420 qdisc noqueue
        inet 10.13.13.1/24 scope global wg0
          valid_lft forever preferred_lft forever

Verifica el estado de WireGuard en el servidor:

    $ docker compose exec server wg show
    interface: wg0
      public key: <clave-pública-del-servidor>
      private key: (hidden)
      listening port: 51820

    peer: <clave-pública-peer1>
      preshared key: (hidden)
      allowed ips: 10.13.13.2/32

    peer: <clave-pública-peer2>
      preshared key: (hidden)
      allowed ips: 10.13.13.3/32


### 2. Arrancar el cliente

    $ make client-setup

Esto copia `server/peer1/peer1.conf` al directorio `client/` y arranca el contenedor cliente con `docker compose up -d client`.

Comprueba la interfaz del cliente:

    $ docker compose exec client ip a show dev peer1
    4: wg0: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1420 qdisc noqueue
        inet 10.13.13.2/32 scope global wg0
          valid_lft forever preferred_lft forever

Comprueba que llegas al servidor a través del túnel:

    $ docker compose exec client ping -c 2 10.13.13.1
    PING 10.13.13.1 (10.13.13.1) 56(84) bytes of data.
    64 bytes from 10.13.13.1: icmp_seq=1 ttl=64 time=0.213 ms
    64 bytes from 10.13.13.1: icmp_seq=2 ttl=64 time=0.198 ms

Verifica que el handshake se ha completado:

    $ docker compose exec client wg show
    interface: peer1
      public key: <clave-pública-peer1>
      private key: (hidden)
      listening port: 51820
      fwmark: 0xca6c

    peer: <clave-pública-del-servidor>
      preshared key: (hidden)
      endpoint: 172.18.0.2:51820
      allowed ips: 0.0.0.0/0, ::/0
      latest handshake: 38 seconds ago
      transfer: 892 B received, 980 B sent


### 3. Conectar el host como cliente VPN (peer2)

Además del contenedor cliente, puedes conectar tu propio host usando el perfil `peer2`.
Antes de usarlo hay que editar dos líneas del fichero generado:

1. `Endpoint = vpn-server:51820` → `Endpoint = 127.0.0.1:51820`
   (el nombre `vpn-server` solo se resuelve dentro de la red Docker; el puerto está publicado en el host)

2. Eliminar la línea `ListenPort = 51820`
   (el puerto ya lo ocupa el proxy de Docker que publica el servidor; como cliente, WireGuard usará un puerto efímero)

Después activa el túnel:

    $ sudo apt install wireguard resolvconf
    $ sudo wg-quick up server/peer2/peer2.conf

Si todo ha ido bien deberías ver la interfaz `peer2` con IP `10.13.13.3`:

    $ p a show dev peer2
    105: peer2: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 65456 qdisc noqueue
        link/none
        inet 10.13.13.3/32 scope global peer2
        valid_lft forever preferred_lft forever

Y deberías poder alcanzar el servidor VPN a través del túnel:

    $ ping -c 2  10.13.13.1
    PING 10.13.13.1 (10.13.13.1) 56(84) bytes of data.
    64 bytes from 10.13.13.1: icmp_seq=1 ttl=64 time=1.10 ms
    64 bytes from 10.13.13.1: icmp_seq=2 ttl=64 time=0.196 ms

Para desconectar:

    $ sudo wg-quick down server/peer2/peer2.conf


## Configuración del servidor (`compose.yml`)

| Variable de entorno | Valor | Descripción |
|---|---|---|
| `SERVERURL` | `vpn-server` | Nombre DNS del servidor (en la red Docker) |
| `SERVERPORT` | `51820` | Puerto UDP de escucha |
| `PEERS` | `2` | Número de perfiles de cliente generados automáticamente |
| `PEERDNS` | `auto` | DNS enviado a los peers (usa el del servidor) |
| `INTERNAL_SUBNET` | `10.13.13.0` | Subred interna de la VPN |


## Diferencias con OpenVPN

| Aspecto | WireGuard | OpenVPN |
|---|---|---|
| Protocolo | UDP exclusivamente | UDP o TCP |
| Autenticación | Clave pública/privada (curva25519) | PKI con certificados X.509 |
| Configuración | Un fichero `.conf` por peer | Perfil `.ovpn` con CA, cert y key incluidos |
| Infraestructura de claves | Sin CA; cada peer tiene su par de claves | CA centralizada (Easy-RSA) |
| Rendimiento | Mayor (kernel nativo) | Menor (espacio de usuario) |
| Revocación de peers | Eliminar el peer del fichero de configuración | Lista de revocación CRL |


## Comandos de referencia

| Comando | Descripción |
|---|---|
| `make server-setup` | Arranca el servidor y genera los perfiles de peers |
| `make client-setup` | Copia peer1.conf al cliente y arranca el contenedor |
| `docker compose exec server wg show` | Estado del servidor: peers y handshakes |
| `docker compose exec client wg show` | Estado del cliente: conexión al servidor |
| `docker compose exec server ip a show dev wg0` | IP del servidor en la VPN |
| `docker compose exec client ip a show dev wg0` | IP del cliente en la VPN |
| `sudo wg-quick up server/peer2/peer2.conf` | Conectar el host como peer2 |
| `sudo wg-quick down server/peer2/peer2.conf` | Desconectar el host |


## Notas

- Los ficheros generados bajo `server/` contienen las claves privadas de todos los peers. No los subas a un repositorio público.
- El perfil de cada peer incluye `AllowedIPs = 0.0.0.0/0`, que encamina **todo** el tráfico por la VPN (full-tunnel). Para split-tunnel, cambia ese valor por las subredes específicas que quieres alcanzar a través de la VPN.
- Para añadir un nuevo peer basta con aumentar `PEERS` en `compose.yml` y regenerar el servidor; los peers existentes conservan sus claves.
- WireGuard no establece conexión permanente: el túnel solo está activo mientras hay intercambio de paquetes. El campo `latest handshake` en `wg show` indica cuándo fue la última comunicación.
