#!/bin/bash
# Laboratorio QoS: 2 clases compitiendo en paralelo
#
# Pipeline que se monta:
#
#   1: (root, htb, default 99)
#    ├── 1:1  (rate 2mbit ceil 2mbit)
#    │    ├── 1:10 (rate 1mbit ceil 2mbit)  <- puerto 5201
#    │    └── 1:20 (rate 1mbit ceil 2mbit)  <- puerto 5202
#    └── 1:99 (rate 100mbit)  <- tráfico por defecto (SSH, fondo...), fuera
#                                del envelope de 2mbit para no afectar a la prueba
#
# Los dos clientes arrancan A LA VEZ y terminan a la vez: competencia
# simétrica (misma cwnd inicial), ambas clases convergen hacia ~1mbit.
#
# Uso:
#   ./pipeline-2class.sh usuario@servidor_remoto

set -e

if [ -z "$1" ]; then
    echo "Uso: $0 usuario@servidor_remoto" >&2
    exit 1
fi
SSH_TARGET="$1"
# El destino puede ser un alias de ~/.ssh/config
# Resuelve el hostname/IP real vía "ssh -G" para que iperf3 pueda resolver
REMOTE_HOST="$(ssh -G "$SSH_TARGET" | awk '/^hostname /{print $2}')"

# ==================== CONFIGURACIÓN ====================
IFACE="enp34s0"

PORT_10=5201
PORT_20=5202

DURATION=10   # duración (segundos) de los dos clientes iperf3

# ==================== FUNCIONES AUXILIARES ====================

snapshot() {
    local label="$1"
    echo ""
    echo "=================================================================="
    echo "  SNAPSHOT: $label   (t=${SECONDS}s desde el inicio del script)"
    echo "=================================================================="
    echo "--- Clases (1:1 padre, 1:10, 1:20) ---"
    echo "\$ sudo tc -s class show dev $IFACE"
    sudo tc -s class show dev "$IFACE"
}

cleanup() {
    ssh "$SSH_TARGET" "pkill -f 'iperf3 -s -p ${PORT_10}'" 2>/dev/null || true
    ssh "$SSH_TARGET" "pkill -f 'iperf3 -s -p ${PORT_20}'" 2>/dev/null || true
}
trap cleanup EXIT

# Desactivar los offloads de segmentación para que el qdisc vea paquetes
# individuales (con TSO/GSO un solo skb agrupa varios segmentos TCP y los
# contadores lended/borrowed no cuadran con los paquetes enviados)
sudo ethtool -K "$IFACE" tso off gso off gro off

# ==================== 1. MONTAJE DEL PIPELINE ====================

# Pasar por fq_codel antes de montar el htb fuerza al kernel a soltar del
# todo el qdisc/clases anteriores, para que las estadísticas (bytes, lended,
# borrowed, overlimits...) arranquen a cero y no arrastren nada previo.
sudo tc qdisc del dev "$IFACE" root 2>/dev/null || echo "   (no había qdisc que borrar)"
sudo tc qdisc add dev "$IFACE" root handle 1: fq_codel
sudo tc qdisc del dev "$IFACE" root
sudo tc qdisc add dev "$IFACE" root handle 1: htb default 99
sudo tc class add dev "$IFACE" parent 1: classid 1:99 htb rate 100mbit
sudo tc class add dev "$IFACE" parent 1: classid 1:1 htb rate 2mbit ceil 2mbit
sudo tc class add dev "$IFACE" parent 1:1 classid 1:10 htb rate 1mbit ceil 2mbit
sudo tc class add dev "$IFACE" parent 1:1 classid 1:20 htb rate 1mbit ceil 2mbit
sudo tc filter add dev "$IFACE" protocol ip parent 1: prio 1 flower \
    ip_proto tcp dst_port "$PORT_10" flowid 1:10
sudo tc filter add dev "$IFACE" protocol ip parent 1: prio 2 flower \
    ip_proto tcp dst_port "$PORT_20" flowid 1:20

snapshot "PARTIDA - pipeline recién montado, contadores a cero"

echo ""
echo "\$ sudo tc -s filter show dev $IFACE"
sudo tc -s filter show dev "$IFACE"

# ==================== 2. ARRANCAR SERVIDORES IPERF3 REMOTOS ====================

echo ""
echo ">>> Arrancando los 2 servidores iperf3 en $SSH_TARGET (vía SSH)..."
ssh -f "$SSH_TARGET" "rm -f /tmp/iperf3_server_${PORT_10}.log; nohup iperf3 -s -p $PORT_10 > /tmp/iperf3_server_${PORT_10}.log 2>&1 &"
ssh -f "$SSH_TARGET" "rm -f /tmp/iperf3_server_${PORT_20}.log; nohup iperf3 -s -p $PORT_20 > /tmp/iperf3_server_${PORT_20}.log 2>&1 &"
sleep 2

# ==================== 3. GENERAR TRÁFICO (1:10 Y 1:20 EN PARALELO) ====================

echo ""
echo ">>> [t=${SECONDS}s] Lanzando los clientes $PORT_10 y $PORT_20 A LA VEZ (competencia simétrica)..."
iperf3 -c "$REMOTE_HOST" -p "$PORT_10" -t "$DURATION" > /tmp/iperf3_client_${PORT_10}.log 2>&1 &
PID_5201=$!
iperf3 -c "$REMOTE_HOST" -p "$PORT_20" -t "$DURATION" > /tmp/iperf3_client_${PORT_20}.log 2>&1 &
PID_5202=$!

# Snapshot a mitad de la prueba, CON el tráfico en curso: es el único
# momento en el que se ven tokens/ctokens negativos y backlog > 0
# (son valores instantáneos; al terminar los clientes, la cola se vacía
# y los buckets se rellenan en milisegundos)
sleep $((DURATION / 2))
snapshot "DURANTE - tráfico en curso"

wait "$PID_5201" 2>/dev/null || true
wait "$PID_5202" 2>/dev/null || true

# ==================== 4. SNAPSHOT FINAL ====================

snapshot "FINAL - totales acumulados de la prueba"

echo ""
echo ">>> Estadísticas del qdisc (HTB) tras la prueba:"
echo "\$ sudo tc -s qdisc show dev $IFACE"
sudo tc -s qdisc show dev "$IFACE"

echo ""
echo ">>> Resultado del cliente $PORT_10:"
echo "\$ iperf3 -c $REMOTE_HOST -p $PORT_10 -t $DURATION"
cat /tmp/iperf3_client_${PORT_10}.log
echo ""
echo ">>> Resultado del cliente $PORT_20:"
echo "\$ iperf3 -c $REMOTE_HOST -p $PORT_20 -t $DURATION"
cat /tmp/iperf3_client_${PORT_20}.log

echo ""
echo "=================================================================="
echo "Guía de lectura de resultados:"
echo ""
echo "  - Ambas clases deberían converger hacia ~1mbit cada una."
echo "  - Con las dos saturadas no queda excedente en 1:1, así que apenas"
echo "    deberían crecer los 'borrowed' de ninguna de las dos."
echo "  - En el snapshot DURANTE, ambas clases deberían mostrar 'tokens'"
echo "    alrededor de 0 o negativos (cada una pegada a su rate, sin poder"
echo "    pedir prestado) y backlog > 0 (el shaper reteniendo paquetes)."
echo "=================================================================="
