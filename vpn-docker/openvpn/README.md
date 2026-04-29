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

```bash
make server-setup
```

Este objetivo ejecuta dos pasos dentro del contenedor servidor:

1. `ovpn_genconfig -u udp://vpn-server` — escribe `openvpn.conf` con el endpoint UDP.
2. `ovpn_initpki` — crea la CA (Easy-RSA), el par de claves DH y la clave TLS-auth.

> El proceso solicita una contraseña para la CA. Anótala; la necesitarás para firmar
> certificados de cliente.

### 2. Arrancar el servidor

```bash
docker compose up -d server
```

Comprueba que escucha en el puerto 1194:

```bash
docker compose logs server
make server-shell
server$ ip a          # debería aparecer una iface tun0 con IP 192.168.255.1
```

### 3. Generar el perfil de cliente

Si no quieres contraseña para la clave privada del cliente:

```bash
make nopass-client1.ovpn
```

Si quieres contraseña:

```bash
make client1.ovpn
```

El perfil se guarda en `docker/client/data/client1.ovpn` e incluye los certificados y claves
(CA, cert, key, tls-auth).


### 4. Arrancar el cliente

```bash
docker compose up -d client
```

El cliente lanza automáticamente `openvpn --config /config/client1.ovpn`. Verifica la conexión:

```bash
make client-shell
client$ ip a                 # ebería aparecer una iface tun0 con IP 192.168.255.0/24
client$ ping 192.168.255.1   # ping al servidor a través del túnel
```

## Revocar un cliente

```bash
make revoke-client
```

Esto invoca `ovpn_revokeclient` dos veces: primero para revocar el certificado (actualiza
`crl.pem`) y luego para eliminar los ficheros del cliente del volumen del servidor.


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

- Los datos del servidor (`pki/`, `openvpn.conf`, etc.) quedan en
  `docker/server/data/conf/` mediante un volumen bind. No borres ese directorio si
  quieres reutilizar la CA.
- El perfil `client1.ovpn` incluye `redirect-gateway def1`, que hace que el cliente encamine
  **todo** su tráfico por la VPN. Para un split-tunnel quita esa línea y añade
  rutas específicas con `push "route ..."` en el servidor.
