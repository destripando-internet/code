#!/bin/bash
# Laboratorio QoS
#
# Pipeline que se monta:
#
#   1: (root, htb)
#    └── 1:1  (rate 2mbit ceil 2mbit)
#         ├── 1:10 (rate 1mbit ceil 2mbit)  <- puerto 5201, SOLO shaper
#         ├── 1:20 (rate 1mbit ceil 2mbit)  <- puerto 5202, SOLO shaper
#         └── 1:30 (rate 1mbit ceil 2mbit)  <- puerto 5203, POLICER (1.5mbit) + shaper
#
# Fases de la prueba:
#   Fase A: solo cliente 5201 activo
#           -> 1:10 puede pedir prestado hasta 2mbit (1:20 y 1:30 ociosas)
#   Fase B: se añade el cliente 5202 mientras 5201 sigue activo
#           -> ambas convergen hacia ~1mbit cada una (préstamo mutuo limitado)
#   Fase C: se añade el cliente 5203 (policer+shaper) mientras las otras dos siguen activas
#           -> se ve el efecto combinado: drops en el filtro (policer) +
#              backlog/overlimits en la clase 1:30 (shaper), con menos margen
#              de préstamo disponible porque 1:10 y 1:20 ya están consumiendo
#
# Uso:
#   ./qos_full_lab.sh usuario@servidor_remoto

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
PORT_30=5203

POLICER_RATE="1.5mbit"
POLICER_BURST="32k"

# Streams TCP paralelos del cliente del puerto 5203: un único stream TCP
# queda limitado por el RTT/ventana muy por debajo del policer, así que se
# usan varios en paralelo para superar POLICER_RATE y forzar descartes
# visibles en el filtro. (UDP habría sido más directo, pero el UDP de
# vuelta entre esta máquina y el host remoto no llega, por firewall/NAT.)
PORT_30_PARALLEL_STREAMS=16

# Duraciones (segundos) de cada fase, medidas desde el arranque de cada cliente
DURATION_5201=45   # arranca en fase A, sigue corriendo hasta el final
DURATION_5202=30   # arranca en fase B
DURATION_5203=20   # arranca en fase C

# Momentos (segundos desde el inicio del script) en los que arranca cada cliente
T_START_5201=0
T_START_5202=15
T_START_5203=30

# ==================== FUNCIONES AUXILIARES ====================

snapshot() {
    local label="$1"
    echo ""
    echo "=================================================================="
    echo "  SNAPSHOT: $label   (t=${SECONDS}s desde el inicio del script)"
    echo "=================================================================="
    echo "--- Clases (1:1 padre, 1:10, 1:20, 1:30) ---"
    echo "\$ sudo tc -s class show dev $IFACE"
    sudo tc -s class show dev "$IFACE"
    echo ""
    echo "--- Filtro con policer (puerto $PORT_30) ---"
    echo "\$ sudo tc -s filter show dev $IFACE"
    sudo tc -s filter show dev "$IFACE" | grep -A5 "police" || echo "(sin datos de policer todavía)"
}

cleanup() {
    ssh "$SSH_TARGET" "pkill -f 'iperf3 -s -p ${PORT_10}'" 2>/dev/null || true
    ssh "$SSH_TARGET" "pkill -f 'iperf3 -s -p ${PORT_20}'" 2>/dev/null || true
    ssh "$SSH_TARGET" "pkill -f 'iperf3 -s -p ${PORT_30}'" 2>/dev/null || true
    # sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
}
trap cleanup EXIT

# ==================== 1. MONTAJE DEL PIPELINE COMPLETO ====================

sudo tc qdisc del dev "$IFACE" root 2>/dev/null || echo "   (no había qdisc que borrar)"
sudo tc qdisc add dev "$IFACE" root handle 1: htb default 10
sudo tc class add dev "$IFACE" parent 1: classid 1:1 htb rate 2mbit ceil 2mbit
sudo tc class add dev "$IFACE" parent 1:1 classid 1:10 htb rate 1mbit ceil 2mbit
sudo tc class add dev "$IFACE" parent 1:1 classid 1:20 htb rate 1mbit ceil 2mbit
sudo tc filter add dev "$IFACE" protocol ip parent 1: prio 1 u32 \
    match ip dport "$PORT_10" 0xffff flowid 1:10
sudo tc filter add dev "$IFACE" protocol ip parent 1: prio 2 u32 \
    match ip dport "$PORT_20" 0xffff flowid 1:20

# Filtro puerto $PORT_30 -> 1:30, CON policer (rate $POLICER_RATE burst $POLICER_BURST drop)..."
sudo tc class add dev "$IFACE" parent 1:1 classid 1:30 htb rate 1mbit ceil 2mbit
sudo tc filter add dev "$IFACE" protocol ip parent 1: prio 3 u32 \
    match ip dport "$PORT_30" 0xffff \
    police rate "$POLICER_RATE" burst "$POLICER_BURST" drop \
    flowid 1:30

echo ""
echo ">>> Pipeline montado:"
echo "\$ sudo tc class show dev $IFACE"
sudo tc class show dev "$IFACE"
echo "\$ sudo tc -s filter show dev $IFACE"
sudo tc -s filter show dev "$IFACE"

# ==================== 2. ARRANCAR SERVIDORES IPERF3 REMOTOS ====================

echo ""
echo ">>> Arrancando los 3 servidores iperf3 en $SSH_TARGET (vía SSH)..."
ssh -f "$SSH_TARGET" "rm -f /tmp/iperf3_server_${PORT_10}.log; nohup iperf3 -s -p $PORT_10 > /tmp/iperf3_server_${PORT_10}.log 2>&1 &"
ssh -f "$SSH_TARGET" "rm -f /tmp/iperf3_server_${PORT_20}.log; nohup iperf3 -s -p $PORT_20 > /tmp/iperf3_server_${PORT_20}.log 2>&1 &"
ssh -f "$SSH_TARGET" "rm -f /tmp/iperf3_server_${PORT_30}.log; nohup iperf3 -s -p $PORT_30 > /tmp/iperf3_server_${PORT_30}.log 2>&1 &"
sleep 2

# ==================== 3. FASE A: solo 5201 ====================

echo ""
echo ">>> [FASE A, t=${SECONDS}s] Lanzando cliente puerto $PORT_10 (único activo, puede tomar hasta 2mbit)..."
iperf3 -c "$REMOTE_HOST" -p "$PORT_10" -t "$DURATION_5201" > /tmp/iperf3_client_${PORT_10}.log 2>&1 &
PID_5201=$!

sleep 8
snapshot "FASE A - solo 5201 activo (esperado: 1:10 pidiendo prestado, 1:20 y 1:30 vacías)"

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

# ==================== 5. FASE C: se añade 5203 (policer + shaper) ====================

REMAINING_TO_C=$((T_START_5203 - SECONDS))
if [ "$REMAINING_TO_C" -gt 0 ]; then
    sleep "$REMAINING_TO_C"
fi

echo ""
echo ">>> [FASE C, t=${SECONDS}s] Lanzando cliente puerto $PORT_30 ($PORT_30_PARALLEL_STREAMS streams TCP en paralelo, por encima del policer $POLICER_RATE)..."
iperf3 -c "$REMOTE_HOST" -p "$PORT_30" -P "$PORT_30_PARALLEL_STREAMS" -t "$DURATION_5203" > /tmp/iperf3_client_${PORT_30}.log 2>&1 &
PID_5203=$!

sleep 8
snapshot "FASE C - las 3 clases activas a la vez (esperado: drops en el policer + backlog/overlimits en 1:30, con poco margen de préstamo por la competencia de 1:10/1:20)"

# ==================== 6. ESPERAR FIN Y SNAPSHOT FINAL ====================

wait "$PID_5203" 2>/dev/null || true
wait "$PID_5202" 2>/dev/null || true
wait "$PID_5201" 2>/dev/null || true

snapshot "FINAL - totales acumulados de toda la prueba"

echo ""
echo ">>> Resultado del cliente 5201 (shaper puro, fase A/B):"
echo "\$ iperf3 -c $REMOTE_HOST -p $PORT_10 -t $DURATION_5201"
cat /tmp/iperf3_client_${PORT_10}.log
echo ""
echo ">>> Resultado del cliente 5202 (shaper puro, fase B):"
echo "\$ iperf3 -c $REMOTE_HOST -p $PORT_20 -t $DURATION_5202"
cat /tmp/iperf3_client_${PORT_20}.log
echo ""
echo ">>> Resultado del cliente 5203 (policer + shaper, fase C):"
echo "\$ iperf3 -c $REMOTE_HOST -p $PORT_30 -P $PORT_30_PARALLEL_STREAMS -t $DURATION_5203"
cat /tmp/iperf3_client_${PORT_30}.log

echo ""
echo "=================================================================="
echo "Guía de lectura de resultados:"
echo ""
echo "FASE A (solo 1:10 activa):"
echo "  - 1:10 debería mostrar 'borrowed' > 0 (toma prestado de 1:1,"
echo "    ya que 1:20 y 1:30 están ociosas) y throughput cercano a 2mbit."
echo ""
echo "FASE B (1:10 + 1:20 activas):"
echo "  - Ambas clases deberían converger hacia ~1mbit cada una,"
echo "    con 'borrowed' reduciéndose porque ya no hay tanto excedente libre."
echo ""
echo "FASE C (1:10 + 1:20 + 1:30 activas):"
echo "  - El filtro del puerto $PORT_30 debería mostrar 'dropped' > 0"
echo "    (el policer descartando lo que excede $POLICER_RATE)."
echo "  - La clase 1:30 debería mostrar 'dropped' en 0 pero 'overlimits'"
echo "    y/o 'backlog' > 0 (el shaper reteniendo, no descartando, dentro"
echo "    de su propio límite de 1-2mbit)."
echo "  - Con 1:10 y 1:20 ya consumiendo su parte, 1:30 tendrá MENOS margen"
echo "    de préstamo disponible que en el experimento aislado anterior,"
echo "    haciendo más visible el efecto de ambos mecanismos (policer +"
echo "    shaper) actuando a la vez sobre el mismo flujo."
echo "=================================================================="
