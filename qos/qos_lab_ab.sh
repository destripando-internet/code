#!/bin/bash
# Laboratorio QoS (solo fases A y B)
#
# Pipeline que se monta:
#
#   1: (root, htb)
#    └── 1:1  (rate 2mbit ceil 2mbit)
#         ├── 1:10 (rate 1mbit ceil 2mbit)  <- puerto 5201, SOLO shaper
#         └── 1:20 (rate 1mbit ceil 2mbit)  <- puerto 5202, SOLO shaper
#
# Fases de la prueba:
#   Fase A: solo cliente 5201 activo
#           -> 1:10 puede pedir prestado hasta 2mbit (1:20 ociosa)
#   Fase B: se añade el cliente 5202 mientras 5201 sigue activo
#           -> ambas convergen hacia ~1mbit cada una (préstamo mutuo limitado)
#
# Uso:
#   ./qos_lab_ab.sh usuario@servidor_remoto

set -e

if [ -z "$1" ]; then
    echo "Uso: $0 usuario@servidor_remoto" >&2
    exit 1
fi
SSH_TARGET="$1"
# El destino puede ser un alias de ~/.ssh/config
# Rresuelve el hostname/IP real vía "ssh -G" para que iperf3 pueda resolver
REMOTE_HOST="$(ssh -G "$SSH_TARGET" | awk '/^hostname /{print $2}')"

# ==================== CONFIGURACIÓN ====================
IFACE="enp34s0"

PORT_10=5201
PORT_20=5202

# Duraciones (segundos) de cada fase, medidas desde el arranque de cada cliente
DURATION_5201=30   # arranca en fase A, sigue corriendo hasta el final
DURATION_5202=15   # arranca en fase B

# Momentos (segundos desde el inicio del script) en los que arranca cada cliente
T_START_5201=0
T_START_5202=15

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
    # sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
}
trap cleanup EXIT

# Desactivar los offloads de segmentación para que el qdisc vea paquetes
# individuales (con TSO/GSO un solo skb agrupa varios segmentos TCP y los
# contadores lended/borrowed no cuadran con los paquetes enviados)
sudo ethtool -K "$IFACE" tso off gso off gro off

# ==================== 1. MONTAJE DEL PIPELINE (A + B) ====================

sudo tc qdisc del dev "$IFACE" root 2>/dev/null || echo "   (no había qdisc que borrar)"
# Pasar por fq_codel antes de montar el htb fuerza al kernel a soltar del
# todo el qdisc/clases anteriores, para que las estadísticas (bytes,
# borrowed, overlimits...) arranquen a cero y no arrastren la prueba previa.
sudo tc qdisc add dev "$IFACE" root handle 1: fq_codel
sudo tc qdisc del dev "$IFACE" root
sudo tc qdisc add dev "$IFACE" root handle 1: htb default 10
sudo tc class add dev "$IFACE" parent 1: classid 1:1 htb rate 2mbit ceil 2mbit
sudo tc class add dev "$IFACE" parent 1:1 classid 1:10 htb rate 1mbit ceil 2mbit
sudo tc class add dev "$IFACE" parent 1:1 classid 1:20 htb rate 1mbit ceil 2mbit

echo ""
echo ">>> Clases definidas:"
echo "\$ sudo tc -s class show dev $IFACE"
sudo tc -s class show dev "$IFACE"

sudo tc filter add dev "$IFACE" protocol ip parent 1: prio 1 flower \
    ip_proto tcp dst_port "$PORT_10" flowid 1:10
sudo tc filter add dev "$IFACE" protocol ip parent 1: prio 2 flower \
    ip_proto tcp dst_port "$PORT_20" flowid 1:20

echo ""
echo ">>> Pipeline montado:"
echo "\$ sudo tc class show dev $IFACE"
sudo tc class show dev "$IFACE"
echo "\$ sudo tc -s filter show dev $IFACE"
sudo tc -s filter show dev "$IFACE"

# ==================== 2. ARRANCAR SERVIDORES IPERF3 REMOTOS ====================

echo ""
echo ">>> Arrancando los 2 servidores iperf3 en $SSH_TARGET (vía SSH)..."
ssh -f "$SSH_TARGET" "rm -f /tmp/iperf3_server_${PORT_10}.log; nohup iperf3 -s -p $PORT_10 > /tmp/iperf3_server_${PORT_10}.log 2>&1 &"
ssh -f "$SSH_TARGET" "rm -f /tmp/iperf3_server_${PORT_20}.log; nohup iperf3 -s -p $PORT_20 > /tmp/iperf3_server_${PORT_20}.log 2>&1 &"
sleep 2

# ==================== 3. FASE A: solo 5201 ====================

echo ""
echo ">>> [FASE A, t=${SECONDS}s] Lanzando cliente puerto $PORT_10 (único activo, puede tomar hasta 2mbit)..."
iperf3 -c "$REMOTE_HOST" -p "$PORT_10" -t "$DURATION_5201" > /tmp/iperf3_client_${PORT_10}.log 2>&1 &
PID_5201=$!

sleep 8
snapshot "FASE A - solo 5201 activo (esperado: 1:10 pidiendo prestado, 1:20 vacía)"

# ==================== 4. FASE B: se añade 5202 ====================

REMAINING_TO_B=$((T_START_5202 - SECONDS))
if [ "$REMAINING_TO_B" -gt 0 ]; then
    sleep "$REMAINING_TO_B"
fi

echo ""
echo ">>> [FASE B, t=${SECONDS}s] Lanzando cliente puerto $PORT_20 (compite con 5201 por el excedente)..."
iperf3 -c "$REMOTE_HOST" -p "$PORT_20" -t "$DURATION_5202" > /tmp/iperf3_client_${PORT_20}.log 2>&1 &
PID_5202=$!

sleep 8
snapshot "FASE B - 5201 y 5202 activos (esperado: ambas clases convergiendo hacia ~1mbit)"

# ==================== 5. ESPERAR FIN Y SNAPSHOT FINAL ====================

wait "$PID_5202" 2>/dev/null || true
wait "$PID_5201" 2>/dev/null || true

snapshot "FINAL - totales acumulados de toda la prueba"

echo ""
echo ">>> Estadísticas del qdisc (HTB) tras la prueba:"
echo "\$ sudo tc -s qdisc show dev $IFACE"
sudo tc -s qdisc show dev "$IFACE"

echo ""
echo ">>> Resultado del cliente 5201 (shaper puro, fase A/B):"
echo "\$ iperf3 -c $REMOTE_HOST -p $PORT_10 -t $DURATION_5201"
cat /tmp/iperf3_client_${PORT_10}.log
echo ""
echo ">>> Resultado del cliente 5202 (shaper puro, fase B):"
echo "\$ iperf3 -c $REMOTE_HOST -p $PORT_20 -t $DURATION_5202"
cat /tmp/iperf3_client_${PORT_20}.log

echo ""
echo "=================================================================="
echo "Guía de lectura de resultados:"
echo ""
echo "FASE A (solo 1:10 activa):"
echo "  - 1:10 debería mostrar 'borrowed' > 0 (toma prestado de 1:1,"
echo "    ya que 1:20 está ociosa) y throughput cercano a 2mbit."
echo ""
echo "FASE B (1:10 + 1:20 activas):"
echo "  - Ambas clases deberían converger hacia ~1mbit cada una,"
echo "    con 'borrowed' reduciéndose porque ya no hay tanto excedente libre."
echo "=================================================================="
