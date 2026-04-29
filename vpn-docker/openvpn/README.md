# Demo OpenVPN con Docker

Demo de un servidor y cliente OpenVPN ejecutándose en contenedores docker.

## Arquitectura

```
  host
  └─ docker network (bridge)
       ├─ openvpn-server  (imagen kylemanna/openvpn)
       │    tun0: 192.168.255.1
       │    puerto UDP 1194 expuesto al host
       └─ openvpn-client  (Dockerfile propio)
            tun0: 192.168.255.x  (asignada por el servidor)
```

La subred de la VPN es `192.168.255.0/24`. El cliente recibe su IP en ese rango al conectarse.


## Estructura de ficheros relevantes

```
openvpn/
├── compose.yml               # Especificación "docker compose"
├── Makefile                  # Reglas para la creación de claves y config
└── docker/
    ├── server/
    │   └── data/conf/        # GENERADO
    │       ├── openvpn.conf  # Configuración del servidor
    │       ├── ovpn_env.sh   # Variables de entorno
    │       ├── crl.pem       # Lista de certificados revocados
    │       └── pki/          # CA, certificados y claves
    └── client/
        ├── Dockerfile        # Imagen cliente (Debian + openvpn)
        └── data/             # GENERADO
            └── client1.ovpn  # Perfil del cliente
```

## Puesta en marcha desde cero

### 1. Inicializar el servidor (solo la primera vez)

Genera la configuración del servidor y la infraestructura PKI (CA, DH, TLS-auth):

    $ make server-setup

Esto ejecuta dos pasos dentro del contenedor `server`:

1. `ovpn_genconfig -u udp://vpn-server` — escribe `openvpn.conf` con el endpoint UDP.
2. `ovpn_initpki` — crea la CA (Easy-RSA), el par de claves DH y la clave TLS-auth.

> El proceso solicita una contraseña para la CA. Anótala; la necesitarás para firmar certificados de cliente.

### 2. Arrancar el servidor

    $ docker compose up -d server
    ✔ Network openvpn_default  Created
    ✔ Container openvpn-server Started

Comprueba que escucha en el puerto 1194:

    $ docker compose logs server

Comprueba su interfaz `tun0`. Debería tener la IP 92.168.255.1

    $ docker compose exec server ip a show dev tun0
    3: tun0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc fq_codel
        link/none
        inet 192.168.255.1 peer 192.168.255.2/32 scope global tun0
          valid_lft forever preferred_lft forever
        inet6 fe80::c586:e778:a764:e2c3/64 scope link stable-privacy
          valid_lft forever preferred_lft forever


### 3. Generar el perfil de cliente

Si no quieres contraseña para la clave privada del cliente (sufiente para esta demo):

    $ make nopass-client1.ovpn

Si quieres contraseña:

    $ make client1.ovpn

El perfil se guarda en `docker/client/data/client1.ovpn` e incluye los certificados y claves (CA, cert, key, tls-auth).


### 4. Arrancar el cliente

    $ docker compose up -d client
    ✔ Container openvpn-client Started

El cliente lanza automáticamente `openvpn --config /config/client1.ovpn`.
Verifica la interaz y su IP (en el rango 192.168.255.0/24):

    $ docker compose exec client ip a show dev tun0
    3: tun0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc fq_codel
        link/none
        inet 192.168.255.6 peer 192.168.255.5/32 scope global tun0
          valid_lft forever preferred_lft forever
        inet6 fe80::873a:1e71:94f3:6433/64 scope link stable-privacy
          valid_lft forever preferred_lft forever

Comprueba que llegas al servidor a través del túnel:

    $ docker compose exec client ping 192.168.255.1 -c 2
    PING 192.168.255.1 (192.168.255.1) 56(84) bytes of data.
    64 bytes from 192.168.255.1: icmp_seq=1 ttl=64 time=0.190 ms
    64 bytes from 192.168.255.1: icmp_seq=2 ttl=64 time=0.279 ms


## Revocar un cliente

    $ make revoke-client

Esto invoca `ovpn_revokeclient` dos veces: primero para revocar el certificado (actualiza `crl.pem`) y luego para eliminar los ficheros del cliente del volumen del servidor.


## Configuración del servidor (`openvpn.conf`)

| Parámetro | Valor | Descripción |
|---|---|---|
| `server` | `192.168.255.0/24` | Subred de la VPN |
| `proto` | `udp` | Protocolo de transporte |
| `port` | `1194` | Puerto de escucha |
| `dev` | `tun0` | Interfaz de túnel (modo routed) |
| `tls-auth` | `pki/ta.key` | HMAC adicional contra DoS/port-scan |
| `push "dhcp-option DNS"` | `8.8.8.8`, `8.8.4.4` | DNS enviado al cliente |
| `redirect-gateway def1` | (en el cliente) | El cliente enruta todo el tráfico por la VPN |


## Comandos de referencia

| Comando | Descripción |
|---|---|
| `make server-setup` | Genera config y PKI del servidor (primera vez) |
| `make nopass-client1.ovpn` | Crea perfil de cliente sin contraseña en la clave |
| `make client1.ovpn` | Crea perfil de cliente con contraseña en la clave |
| `make revoke-client` | Revoca el certificado de `client1` |
| `make server-shell` | Abre shell en el contenedor servidor |
| `make client-shell` | Abre shell en el contenedor cliente |


## Notas

- Los datos del servidor (`pki/`, `openvpn.conf`, etc.) quedan en `docker/server/data/conf/` mediante un volumen bind. No borres ese directorio si quieres reutilizar la CA.
- El perfil `client1.ovpn` incluye `redirect-gateway def1`, que hace que el cliente encamine  **todo** su tráfico por la VPN. Para un split-tunnel quita esa línea y añade rutas específicas con `push "route ..."` en el servidor.
