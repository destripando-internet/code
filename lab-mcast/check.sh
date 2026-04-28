clear

docker exec r1 sysctl net.ipv4.ip_forward
docker exec r1 sysctl net.ipv4.conf.all.mc_forwarding
docker exec r1 grep yes /etc/frr/daemons
docker exec r1 ps fax
docker exec r1 vtysh -c "show running-config"

docker exec r1 vtysh -c "show ip mroute"
docker exec r2 vtysh -c "show ip mroute"
docker exec r3 vtysh -c "show ip mroute"

echo -e "\n-- ifaces"
echo R1
docker exec r1 ip -o -4 addr show | awk '$2 != "lo" {print $2, $4}'

echo R2
docker exec r2 ip -o -4 addr show | awk '$2 != "lo" {print $2, $4}'

echo R3
docker exec r3 ip -o -4 addr show | awk '$2 != "lo" {print $2, $4}'

echo -e "\n-- PIM neighbors"
docker exec r1 vtysh -c "show ip pim neighbor"
docker exec r2 vtysh -c "show ip pim neighbor"
docker exec r3 vtysh -c "show ip pim neighbor"
