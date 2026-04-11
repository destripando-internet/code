#!/usr/bin/env python3
"""
Lab Routing Delta — Mininet Topology
Equivalent to the docker-compose lab-routing-delta lab.

Topology:
  r1  — N0 (10.0.0.3/24), N1 (10.0.1.2/24), N4 (10.0.4.2/24)
  r2  — N1 (10.0.1.3/24), N2 (10.0.2.2/24)
  r3  — N2 (10.0.2.3/24), N3 (10.0.3.2/24), N4 (10.0.4.3/24)
  server — N3 (10.0.3.3/24)

Usage:
  sudo python3 topology.py [--static | --rip | --ospf | --eigrp]
"""

import argparse
import os
import signal
import sys
import time

from mininet.cli import CLI
from mininet.log import info, setLogLevel
from mininet.net import Mininet
from mininet.node import Node, OVSSwitch

LAB_DIR = os.path.dirname(os.path.abspath(__file__))
FRR_RUN_BASE = '/tmp/frr'


class Router(Node):
    def config(self, **params):
        super().config(**params)
        self.cmd('sysctl -w net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super().terminate()


class LabTopology:

    def __init__(self):
        self.net = Mininet(switch=OVSSwitch, waitConnected=True)

    def build(self):
        info('*** Adding routers\n')
        self.r1     = self.net.addHost('r1',     cls=Router, ip=None)
        self.r2     = self.net.addHost('r2',     cls=Router, ip=None)
        self.r3     = self.net.addHost('r3',     cls=Router, ip=None)
        self.server = self.net.addHost('server', ip=None)

        info('*** Adding network segments (N0–N4)\n')
        N0 = self.net.addSwitch('N0', failMode='standalone')
        N1 = self.net.addSwitch('N1', failMode='standalone')
        N2 = self.net.addSwitch('N2', failMode='standalone')
        N3 = self.net.addSwitch('N3', failMode='standalone')
        N4 = self.net.addSwitch('N4', failMode='standalone')

        info('*** Adding links\n')
        r1, r2, r3, server = self.r1, self.r2, self.r3, self.server

        #           node    segment  interface       IP/prefix
        self.net.addLink(r1, N0, intfName1='r1-eth0', params1={'ip': '10.0.0.3/24'})
        self.net.addLink(r1, N1, intfName1='r1-eth1', params1={'ip': '10.0.1.2/24'})
        self.net.addLink(r1, N4, intfName1='r1-eth2', params1={'ip': '10.0.4.2/24'})

        self.net.addLink(r2, N1, intfName1='r2-eth0', params1={'ip': '10.0.1.3/24'})
        self.net.addLink(r2, N2, intfName1='r2-eth1', params1={'ip': '10.0.2.2/24'})

        self.net.addLink(r3, N2, intfName1='r3-eth0', params1={'ip': '10.0.2.3/24'})
        self.net.addLink(r3, N3, intfName1='r3-eth1', params1={'ip': '10.0.3.2/24'})
        self.net.addLink(r3, N4, intfName1='r3-eth2', params1={'ip': '10.0.4.3/24'})

        self.net.addLink(server, N3, intfName1='server-eth0', params1={'ip': '10.0.3.3/24'})

    def start(self):
        self.net.start()

        info('*** Removing default routes\n')
        for node in self.net.hosts:
            node.cmd('ip route del default 2>/dev/null; true')

        info('*** Starting FRR zebra on routers\n')
        for router in (self.r1, self.r2, self.r3):
            self._start_zebra(router)

        self.server.cmd('ip route add default via 10.0.3.2')

    def run(self, routing=None):
        if routing:
            getattr(self, f'setup_{routing}')()

        try:
            CLI(self.net)
        finally:
            info('*** Stopping FRR daemons\n')
            for router in (self.r1, self.r2, self.r3):
                self._stop_frr(router.name)
            self.net.stop()

    def setup_static(self):
        self.r1.cmd('ip route add default via 10.0.4.3')
        self.r2.cmd('ip route add 10.0.0.0/24 via 10.0.1.2')
        self.r2.cmd('ip route add default via 10.0.2.3')
        self.r3.cmd('ip route add default via 10.0.4.2')

    def setup_rip(self):
        for router, conf in ((self.r1, 'R1-ripd.conf'),
                             (self.r2, 'R2-ripd.conf'),
                             (self.r3, 'R3-ripd.conf')):
            self._start_daemon('ripd', router, f'{LAB_DIR}/rip/{conf}')

    def setup_ospf(self):
        for router in (self.r1, self.r2, self.r3):
            self._start_daemon('ospfd', router, f'{LAB_DIR}/ospfd.conf')

    def setup_eigrp(self):
        for router in (self.r1, self.r2, self.r3):
            self._start_daemon('eigrpd', router, f'{LAB_DIR}/eigrpd.conf')

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _start_zebra(self, router):
        run_dir = f'{FRR_RUN_BASE}-{router.name}'
        os.makedirs(run_dir, exist_ok=True)

        conf = f'{run_dir}/zebra.conf'
        if not os.path.exists(conf):
            with open(conf, 'w') as f:
                f.write('!\n')

        router.cmd(
            f'/usr/lib/frr/zebra'
            f' -f {conf}'
            f' -i {run_dir}/zebra.pid'
            f' -z {run_dir}/zserv.api'
            f' -d'
            f' > {run_dir}/zebra.log 2>&1'
        )
        time.sleep(0.4)

    def _start_daemon(self, daemon, router, conf):
        run_dir = f'{FRR_RUN_BASE}-{router.name}'
        router.cmd(
            f'/usr/lib/frr/{daemon}'
            f' -f {conf}'
            f' -i {run_dir}/{daemon}.pid'
            f' -z {run_dir}/zserv.api'
            f' -d'
        )

    def _stop_frr(self, router_name):
        run_dir = f'{FRR_RUN_BASE}-{router_name}'
        for daemon in ('eigrpd', 'ospfd', 'ripd', 'zebra'):
            pid_file = f'{run_dir}/{daemon}.pid'
            try:
                with open(pid_file) as f:
                    os.kill(int(f.read().strip()), signal.SIGTERM)
            except (FileNotFoundError, ValueError, ProcessLookupError, OSError):
                pass


if __name__ == '__main__':
    if os.geteuid() != 0:
        print('Run as root:  sudo python3 topology.py', file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Lab Routing Delta')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--static', action='store_true', help='configure static routes')
    group.add_argument('--rip',    action='store_true', help='start FRR ripd on all routers')
    group.add_argument('--ospf',   action='store_true', help='start FRR ospfd on all routers')
    group.add_argument('--eigrp',  action='store_true', help='start FRR eigrpd on all routers')
    args = parser.parse_args()

    routing = next((k for k in ('static', 'rip', 'ospf', 'eigrp') if getattr(args, k)), None)

    setLogLevel('info')
    lab = LabTopology()
    lab.build()
    lab.start()
    lab.run(routing)
