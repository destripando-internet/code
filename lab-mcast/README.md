# Laboratorio PIM-SM con la topología Delta

Este documento explica un laboratorio muy práctico (con implementaciones reales) del protocolo de encaminamiento dinámico multicast PIM-SM.

Docs:

- https://docs.frrouting.org/en/stable-10.5/pim.html
- https://docs.frrouting.org/en/stable-10.5/ospfd.html

## Topología

<img src="topology.png" width="90%">


## Descripción

El escenario propuesto implica un emisor mcast en `node2` y un receptor en `node3`. Por tanto el FHR (First Hop Router) es R2 y el LHR (Last Hop Router) es R3. El RP (Rendezvous Point), que es el nombre que PIM da al router núcleo, será R1 ( 10.0.4.2).

Se ofrecen dos métodos para la elección del RP: Auto-RP y BSR (BootStrap Router), aunque como solo R1 está configurado como candidato, siempre se le elegirá a él. Esto se puede ver respectivamente en `router/autorp-r1.conf` y `router/bsr-r1.conf`.

Setup con Auto-RP:

    $ make autorp

Setup con BSR:

    $ make bsr


### Encaminamiento OSPF

PIM requiere un protocolo de encaminamiento unicast para descubrir todos los routers y redes de la subred. Para eso tenemos configurado OSPF en todos los routers.

Lo primero es esperar que el protocolo converja:

    $ ping 10.0.5.3
    From 10.0.0.3 icmp_seq=4 Destination Net Unreachable
    From 10.0.0.3 icmp_seq=43 Destination Net Unreachable
    64 bytes from 10.0.5.3: icmp_seq=49 ttl=62 time=0.091 ms
    64 bytes from 10.0.5.3: icmp_seq=50 ttl=62 time=0.066 ms
    ^C

Así puedes ver la unicast:

    $ docker exec r1 vtysh -c "show ip route ospf"

    O   10.0.0.0/24 [110/10] is directly connected, eth0, weight 1, 00:03:18
    O   10.0.1.0/24 [110/10] is directly connected, eth1, weight 1, 00:03:18
    O>* 10.0.2.0/24 [110/20] via 10.0.1.3, eth1, weight 1, 00:02:23
      *                      via 10.0.4.3, eth2, weight 1, 00:02:23
    O>* 10.0.3.0/24 [110/20] via 10.0.4.3, eth2, weight 1, 00:02:23
    O   10.0.4.0/24 [110/10] is directly connected, eth2, weight 1, 00:03:18
    O>* 10.0.5.0/24 [110/20] via 10.0.1.3, eth1, weight 1, 00:02:28

Vecinos OSPF:

    $ docker exec r1 vtysh -c "show ip ospf neighbor"
    Neighbor ID Pri  State    Up Time  Dead  Time  Address   Interface
    10.0.5.2      1  Full/DR  3m05s      39. 223s  10.0.1.3  eth1:10.0.1.2
    10.0.4.3      1  Full/DR  3m00s      39. 223s  10.0.4.3  eth2:10.0.4.2

### Vecinos PIM

    $ docker exec r1 vtysh -c "show ip pim neighbor"
     Interface  Neighbor  Uptime    Holdtime  DR Pri
     eth1       10.0.1.3  00:03:47  00:01:27  1
     eth2       10.0.4.3  00:03:47  00:01:27  1


### Auto-RP

Comprobación del proceso Auto-RP (si has ejecutado `make autorp`).

R1 anuncia su candidatura como RP y R3 actúa como Mapping Agent. Todos los routers descubren el RP dinámicamente.

Estado del Candidate RP (R1):

    $ docker exec r1 vtysh -c "show ip pim autorp"
    AutoRP Discovery is enabled

    Discovered RP's (count=1)
     RP address  Group Range
     10.0.4.2     224.0.0.0/4

    AutoRP Announcement is enabled
      interval 5s scope 31 holdtime 15s

    Candidate RP's (count=1)
     RP address  Group Range  Prefix-List
     10.0.4.2    224.0.0.0/4  -

    AutoRP Mapping-Agent is disabled

Estado del Mapping Agent (R3):

    $ docker exec r3 vtysh -c "show ip pim autorp"
    AutoRP Discovery is enabled

    Discovered RP's (count=1)
     RP address  Group Range
     10.0.4.2     224.0.0.0/4

    AutoRP Announcement is disabled

    AutoRP Mapping-Agent is enabled
      interval 5s scope 31 holdtime 180s
      source 10.0.4.3 (explicit address)

    Advertised RP's (count=1)
     RP address  Group Range
     10.0.4.2     224.0.0.0/4


#### RP info

El campo `Source=AutoRP` confirma que el RP se ha descubierto correctamente:

    $ docker exec r1 vtysh -c "show ip pim rp-info"
     RP address  group/prefix-list  OIF   I am RP  Source  Group-Type
     10.0.4.2    224.0.0.0/4        eth2  yes      AutoRP  ASM

    $ docker exec r2 vtysh -c "show ip pim rp-info"
    RP address  group/prefix-list  OIF   I am RP  Source  Group-Type
    10.0.4.2    224.0.0.0/4        eth0  no       AutoRP  ASM

    $ docker exec r3 vtysh -c "show ip pim rp-info"
    RP address  group/prefix-list  OIF   I am RP  Source  Group-Type
    10.0.4.2    224.0.0.0/4        eth2  no       AutoRP  ASM


### BSR (BootStrap Router)

Aplica si has ejecutado `make bsr`.

R1 es el Candidate RP y R3 el Candidate BSR. Los mensajes Bootstrap se propagan en `224.0.0.13` (ALL-PIM-ROUTERS) usando PIM directamente.

Estado en el BSR electo (R3):

    $ docker exec r3 vtysh -c "show ip pim bsr"
    Current preferred BSR address: 10.0.4.3
    Priority        Fragment-Tag    State            UpTime
    64              20277           BSR_ELECTED      00:00:16

Estado en un router no-BSR (R2):

    $ docker exec r2 vtysh -c "show ip pim bsr"
    Current preferred BSR address: 10.0.4.3
    Priority        Fragment-Tag    State               UpTime
    64              20280           ACCEPT_PREFERRED    00:00:15

El campo `Source=BSR` en `rp-info` confirma la convergencia:

    $ docker exec r2 vtysh -c "show ip pim rp-info"
    RP address  group/prefix-list  OIF   I am RP  Source  Group-Type
    10.0.4.2    224.0.0.0/4        eth0  no       BSR     ASM


### PIM interfaces

    $ docker exec r1 vtysh -c "show ip pim interface"
     Interface  State  Address   PIM Nbrs  PIM DR    FHR  IfChannels
     eth0       up     10.0.0.3  0         local     0    2
     eth1       up     10.0.1.2  1         10.0.1.3  0    2
     eth2       up     10.0.4.2  1         10.0.4.3  0    4
     pimreg     up     0.0.0.0   0         local     0    0


### Grupos IGMP en el LHR (R3)

    $ docker exec r3 vtysh -c "show ip igmp groups"
    Interface        Group           Mode Timer    Srcs V Uptime
    eth0             224.0.1.39      EXCL 00:03:08    1 3 00:03:53
    eth0             224.0.1.40      EXCL 00:03:08    1 3 00:03:53
    eth1             224.0.1.39      EXCL 00:03:10    1 3 00:03:53
    eth1             224.0.1.40      EXCL 00:03:10    1 3 00:03:53
    eth2             224.0.1.39      EXCL 00:03:10    1 3 00:03:53
    eth2             224.0.1.40      EXCL 00:03:10    1 3 00:03:53

Estos grupos mcast se utilizan para los mensajes de descubrimiento y anuncio de candidatos RP.

### Tabla de encaminamiento mcast

De momento no hay transmisión de datos mcast.

    $ docker exec r1 vtysh -c "show ip mroute"
    IP Multicast Routing Table
    Flags: S - Sparse, D - Dense, C - Connected, P - Pruned
        R - SGRpt Pruned, F - Register flag, T - SPT-bit set
    Source    Group            Flags  Proto  Input  Output  TTL  Uptime
    *         224.0.1.39       SC     IGMP   eth2   pimreg  1    00:04:51
                                      IGMP          eth0    1
                                      IGMP          eth1    1
    *         224.0.1.40       SC     IGMP   eth2   pimreg  1    00:04:51
                                      IGMP          eth0    1
                                      IGMP          eth1    1
    10.0.0.1  239.255.255.250  SFTP   none   eth0   none    0    --:--:--


    $ docker exec r2 vtysh -c "show ip mroute"
    Source  Group       Flags  Proto  Input  Output  TTL  Uptime
    *       224.0.1.39  SC     IGMP   eth0   pimreg  1    00:04:57
                               IGMP          eth0    1
                               IGMP          eth2    1
    *       224.0.1.40  SC     IGMP   eth0   pimreg  1    00:04:57
                               IGMP          eth0    1
                               IGMP          eth2    1


    $ docker exec r3 vtysh -c "show ip mroute"
    Source  Group       Flags  Proto  Input  Output  TTL  Uptime
    *       224.0.1.39  SC     IGMP   eth2   pimreg  1    00:06:35
                               IGMP          eth0    1
                               IGMP          eth1    1
                               IGMP          eth2    1
    *       224.0.1.40  SC     IGMP   eth2   pimreg  1    00:06:35
                               IGMP          eth0    1
                               IGMP          eth1    1
                               IGMP          eth2    1


### Estudiando una transmisión mcast con iperf

Ejecutamos un suscriptor del grupo 239.1.1.1 en `node3`:

    $ docker exec node3 iperf -s -u -B 239.1.1.1 &
    Server listening on UDP port 5001
    Joining multicast group  239.1.1.1

`node3` envía IGMP Membership Report para unirse al grupo. El grupo aparece en `R3`.

    $ docker exec r3 vtysh -c "show ip igmp groups"
    [solo se muestran los cambios]
    Interface        Group           Mode Timer    Srcs V Uptime
    eth1             239.1.1.1       EXCL 00:04:01    1 3 00:00:46

`R3` crea (*,G) en su tabla de rutas mcast porque aún se desconoce la fuente. El flag `C` indica que hay un miembro del grupo directamente conectado a una de sus interfaces (el `iperf` que acabamos de arrancar).

    $ docker exec r3 vtysh -c "show ip mroute"
    [solo se muestran los cambios]
    Source  Group       Flags  Proto  Input  Output  TTL  Uptime
    *       239.1.1.1   SC     IGMP   eth2   pimreg  1    00:01:20
                               IGMP          eth1    1

`R3` envía PIM Join al RP (R1). `R1` crea esa entrada en el RPT.

    $ docker exec r1 vtysh -c "show ip mroute"
    [solo se muestran los cambios]
    Source    Group            Flags  Proto  Input  Output  TTL  Uptime
    *         239.1.1.1        S      none   eth2   none    0    --:--:--

Arrancamos un emisor mcast en `node2` para ese grupo:

    $ docker exec node2 iperf -c 239.1.1.1 -u -t 5 -T 64 &
    ------------------------------------------------------------
    Client connecting to 239.1.1.1, UDP port 5001
    Sending 1470 byte datagrams, IPG target: 11215.21 us (kalman adjust)
    UDP buffer size:  208 KByte (default)
    ------------------------------------------------------------
    [  1] local 10.0.5.3 port 40221 connected with 239.1.1.1 port 5001
    [  1] local 239.1.1.1 port 5001 connected with 10.0.5.3 port 40221

`node2` envía el tráfico a su FHR (R2). `R2` ahora conoce la fuente y configura (S,G). Envía el tráfico con PIM Register (unicast) al RP (R1). El flag `F` indica justo esa situación (Register Flag).

    $ docker exec r2 vtysh -c "show ip mroute"
    [solo se muestran los cambios]
    Source    Group       Flags  Proto  Input  Output  TTL  Uptime
    10.0.5.3  239.1.1.1   SF     PIM    eth2   eth0    1    00:00:23

`R1` crea la entrada (S,G) y reenvía los mensajes a través del RPT, que es el SPT de `R1`. Por eso aparece el flag `T`.

    $ docker exec r1 vtysh -c "show ip mroute"
    [solo se muestran los cambios]
    Source    Group       Flags  Proto  Input  Output  TTL  Uptime
    10.0.5.3  239.1.1.1   ST     STAR   eth1   eth2    1    00:00:20

La tabla de `R3` confirma que el tráfico está llegando a través del RPT porque no existe la fila (S,G). También puedes comprobar que la interfaz de entrada es `eth1` (que lo conecta con el RP) y la de salida es eth1 (que lo lleva a `node3`).

    $ docker exec r3 vtysh -c "show ip mroute"
    [solo se muestran los cambios]
    Source  Group       Flags  Proto  Input  Output  TTL  Uptime
    *       239.1.1.1   SC     IGMP   eth2   eth1    1    00:01:08


#### SPT Switchover

La distribución anterior ha utilizado el árbol núcleo (RPT) en todo momento porque la configuración de `R3` dice:

    spt-switchover infinity-and-beyond

Es decir, la tasa umbral para conmutar a SPT es infinito. Nunca hará la conmutación. Desactiva ahora esa configuración:

    $ docker exec r3 vtysh -c "conf t" -c "router pim" -c "no spt-switchover infinity-and-beyond"

Ahora, el cambio se producirá en cuanto haya tráfico. Repite el envío:

    $ docker exec node2 iperf -c 239.1.1.1 -u -t 5 -T 64 &

En cuanto llega el primer mensaje mcast a `R3`, este efectua el 'SPT switchover' y envía PIM Join a `R2`. Cuando `R3` recibe tráfico por el SPT (R2->R3) envía (S,G,rpt) Prune al RP para podar el RPT. `R1` envia PIM Register-Stop a `R2` para que deje de enviarle el tráfico de ese grupo.

Puedes comprobar la tabla de `R1`. El flag `R` indica que está cortado (pruned) y `R1` ya no está enviando tráfico para ese grupo específico. El flag `P` indica que no hay ningún receptor alcanzable por esa interfaz.

    $ docker exec r1 vtysh -c "show ip mroute"
    [solo se muestran los cambios]
    Source    Group            Flags  Proto  Input  Output  TTL  Uptime
    *         239.1.1.1        S      none   eth2   none    0    --:--:--
    10.0.5.3  239.1.1.1        SRP    none   eth1   none    0    --:--:--

 En `R3` el flag `T` indica que el tráfico está llegando ahora a través del SPT de `R2`, y que la interfaz de entrada ahora sea `eth0` (que lo conecta con `R2`) lo confirma.

    $ docker exec r3 vtysh -c "show ip mroute"
    [solo se muestran los cambios]
    Source    Group       Flags  Proto  Input  Output  TTL  Uptime
    10.0.5.3  239.1.1.1   ST     STAR   eth0   eth1    1    00:01:37

Como podrás imaginar la opción `spt-switchover` permite valores intermedios entre 0 (que es el valor por defecto) e infinito. Esta opción acepta un tasa umbral arbitraria. La idea es decidir cuando vale la pena crear un SPT específico para un transmisión. Si la tasa es baja (decisión arbitraria) es globalmente más eficiente utilizar el árbol núcleo. Pero cuando la tasa supera el umbral, es mejor enviar el tráfico directamente desde el FHR y así evitar una carga de tráfico significativa a otras partes de la red.


### Capturar tráfico PIM

Por supuesto, es posible capturar todos los mensajes IGMP y PIM mencionados:

PIM Hello y Join/Prune en el enlace R1–R3 (N4):

    $ docker exec r1 tshark -i any -Y pim
    10.0.4.3 → 224.0.0.13   PIMv2 72 Bootstrap
    10.0.4.2 → 10.0.4.3     PIMv2 58 Candidate-RP-Advertisement
    10.0.1.2 → 224.0.0.13   PIMv2 72 Bootstrap
    10.0.4.2 → 224.0.0.13   PIMv2 72 Bootstrap
    10.0.1.3 → 224.0.0.13   PIMv2 72 Bootstrap
    10.0.0.3 → 224.0.0.13   PIMv2 70 Hello
    10.0.1.2 → 224.0.0.13   PIMv2 70 Hello
    10.0.0.3 → 224.0.0.22   IGMPv3 96 Membership Report / Join
    10.0.1.3 → 224.0.0.13   PIMv2 70 Hello
    10.0.1.2 → 224.0.0.13   PIMv2 70 Join/Prune
    10.0.1.3 → 224.0.0.13   PIMv2 90 Join/Prune
    10.0.5.3 → 239.1.1.1    PIMv2 64 Register
    10.0.4.2 → 10.0.5.2     PIMv2 54 Register-stop
    10.0.4.2 → 10.0.0.3     PIMv2 54 Register-stop
