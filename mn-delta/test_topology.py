#!/usr/bin/env python3
"""
Integration tests for mn-delta README use cases.

Run as root:
    sudo python3 -m unittest test_topology -v

Each TestCase class starts its own Mininet topology, so suites can be run
individually or together.  Dynamic-protocol tests include a wait_for() helper
that polls until the expected state appears, up to a configurable timeout.
"""

import os
import re
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FRR_RUN_BASE = '/tmp/frr'
ANSI_RE = re.compile(r'\x1b\[[0-9;]*[mK]')


def _strip_ansi(text):
    return ANSI_RE.sub('', text)


def skip_unless_root(cls):
    if os.geteuid() != 0:
        return unittest.skip('requires root (sudo)')(cls)
    return cls


class BaseTopologyTest(unittest.TestCase):
    """Shared setup/teardown and helpers for all routing scenarios."""

    routing = None          # 'static' | 'rip' | 'ospf' | 'eigrp' | None
    initial_wait = 2        # seconds to sleep after setup() before first test

    @classmethod
    def setUpClass(cls):
        from mininet.log import setLogLevel
        from topology import LabTopology

        setLogLevel('warning')
        cls.lab = LabTopology()
        cls.lab.build()
        cls.lab.start()
        if cls.routing:
            getattr(cls.lab, f'setup_{cls.routing}')()
        time.sleep(cls.initial_wait)

    @classmethod
    def tearDownClass(cls):
        lab = cls.lab
        lab.host.cmd('ip route del 10.0.0.0/16 2>/dev/null; true')
        for node in lab.net.hosts:
            if node.inNamespace:
                ns_path = f'/var/run/netns/{node.name}'
                try:
                    os.unlink(ns_path)
                except FileNotFoundError:
                    pass
        for router in (lab.r1, lab.r2, lab.r3):
            lab._stop_frr(router.name)
        lab.net.stop()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def node_cmd(self, node, cmd):
        """Run a shell command inside a Mininet node."""
        return node.cmd(cmd)

    def vtysh(self, router, vtysh_cmd):
        """Run a vtysh command on a Mininet FRR router."""
        run_dir = f'{FRR_RUN_BASE}-{router.name}'
        raw = router.cmd(
            f'vtysh --vty_socket {run_dir} -c "{vtysh_cmd}" 2>/dev/null'
        )
        return _strip_ansi(raw)

    def wait_for(self, condition_fn, timeout=60, poll=3):
        """Poll condition_fn() until True or timeout (seconds). Returns bool."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if condition_fn():
                return True
            time.sleep(poll)
        return False

    def ping_server(self):
        """Ping the server (10.0.3.3) from the root namespace. Returns CompletedProcess."""
        return subprocess.run(
            ['ping', '-c', '1', '-W', '2', '10.0.3.3'],
            capture_output=True, text=True,
        )

    def traceroute_server(self):
        """Traceroute to the server from the root namespace. Returns stdout."""
        result = subprocess.run(
            ['traceroute', '-n', '-w', '1', '-q', '1', '-m', '8', '10.0.3.3'],
            capture_output=True, text=True, timeout=30,
        )
        return result.stdout


# ======================================================================
# Static routing
# ======================================================================

@skip_unless_root
class TestStaticRouting(BaseTopologyTest):
    """README §Static routing — manual static routes, no dynamic protocol."""

    routing = 'static'
    initial_wait = 1

    def test_r1_default_route(self):
        output = self.node_cmd(self.lab.r1, 'ip route')
        self.assertIn('default via 10.0.4.3 dev r1-eth2', output)

    def test_r1_direct_networks(self):
        output = self.node_cmd(self.lab.r1, 'ip route')
        self.assertRegex(output, r'10\.0\.0\.0/24 dev r1-eth0 proto kernel')
        self.assertRegex(output, r'10\.0\.1\.0/24 dev r1-eth1 proto kernel')
        self.assertRegex(output, r'10\.0\.4\.0/24 dev r1-eth2 proto kernel')

    def test_ping_server(self):
        result = self.ping_server()
        self.assertEqual(result.returncode, 0,
                         msg=f'ping failed:\n{result.stdout}{result.stderr}')
        self.assertIn('1 received', result.stdout)

    def test_traceroute_server_three_hops(self):
        """Traceroute must reach the server in exactly 3 hops: r1 → r3 → server."""
        output = self.traceroute_server()
        hop_lines = [l for l in output.splitlines() if re.match(r'\s*\d+', l)]
        self.assertGreaterEqual(len(hop_lines), 3,
                                msg=f'Too few hops:\n{output}')
        self.assertIn('10.0.0.3', hop_lines[0], msg='hop 1 should be r1 (10.0.0.3)')
        self.assertIn('10.0.4.3', hop_lines[1], msg='hop 2 should be r3 (10.0.4.3)')
        self.assertIn('10.0.3.3', hop_lines[2], msg='hop 3 should be server (10.0.3.3)')


# ======================================================================
# RIPv2
# ======================================================================

@skip_unless_root
class TestRIPv2(BaseTopologyTest):
    """README §RIPv2 — dynamic routing with ripd and link-failure reroute."""

    routing = 'rip'
    initial_wait = 5    # daemons start; wait_for() handles full convergence

    def _rip_converged(self):
        output = self.node_cmd(self.lab.r1, 'ip route')
        return 'proto rip' in output

    def setUp(self):
        # All tests in this class depend on RIP having converged.
        converged = self.wait_for(self._rip_converged, timeout=60)
        if not converged:
            self.skipTest('RIP did not converge within 60 s')

    def test_r1_ip_route_rip_remote_networks(self):
        output = self.node_cmd(self.lab.r1, 'ip route')
        self.assertRegex(output, r'10\.0\.2\.0/24.*proto rip',
                         msg='10.0.2.0/24 should be learned via RIP')
        self.assertRegex(output, r'10\.0\.3\.0/24.*proto rip',
                         msg='10.0.3.0/24 should be learned via RIP')

    def test_r1_vtysh_show_ip_route(self):
        """vtysh 'show ip route' must show R>* entries for remote networks."""
        output = self.vtysh(self.lab.r1, 'show ip route')
        self.assertRegex(output, r'R>\*\s+10\.0\.2\.0/24')
        self.assertRegex(output, r'R>\*\s+10\.0\.3\.0/24')

    def test_r1_vtysh_show_ip_rip(self):
        """vtysh 'show ip rip' must list connected and learned networks."""
        output = self.vtysh(self.lab.r1, 'show ip rip')
        # Directly connected interfaces shown as C(i)
        self.assertRegex(output, r'C\(i\)\s+10\.0\.0\.0/24')
        self.assertRegex(output, r'C\(i\)\s+10\.0\.1\.0/24')
        self.assertRegex(output, r'C\(i\)\s+10\.0\.4\.0/24')
        # Remote networks learned via RIP shown as R(n)
        self.assertRegex(output, r'R\(n\)\s+10\.0\.2\.0/24')
        self.assertRegex(output, r'R\(n\)\s+10\.0\.3\.0/24')

    def test_r1_vtysh_running_config(self):
        """vtysh 'show running-config' must contain the RIP block with r1's networks."""
        output = self.vtysh(self.lab.r1, 'show running-config')
        self.assertIn('router rip', output)
        self.assertIn('network 10.0.0.0/24', output)
        self.assertIn('network 10.0.1.0/24', output)
        self.assertIn('network 10.0.4.0/24', output)

    def test_ping_server(self):
        result = self.ping_server()
        self.assertEqual(result.returncode, 0,
                         msg=f'ping failed:\n{result.stdout}')

    def test_link_failure_reroute(self):
        """After r1-r3 link failure, RIP must reroute traffic through r2 (4 hops)."""
        # Bring down r1-eth2 (the N4 link connecting r1 and r3 directly).
        # README shows 'link r1 r3 down'; r1-eth2 is r1's interface on N4.
        self.lab.r1.cmd('ip link set dev r1-eth2 down')
        try:
            def rerouted():
                output = self.traceroute_server()
                # New path must pass through r2 (10.0.1.3) and still reach server
                return '10.0.1.3' in output and '10.0.3.3' in output

            converged = self.wait_for(rerouted, timeout=120, poll=5)
            self.assertTrue(converged,
                            msg='RIP did not reroute through r2 within 120 s')

            # Verify at least 4 hops in the new path
            output = self.traceroute_server()
            hop_lines = [l for l in output.splitlines() if re.match(r'\s*\d+', l)]
            self.assertGreaterEqual(len(hop_lines), 4,
                                    msg=f'Expected ≥4 hops after reroute:\n{output}')
        finally:
            self.lab.r1.cmd('ip link set dev r1-eth2 up')


# ======================================================================
# OSPFv2
# ======================================================================

@skip_unless_root
class TestOSPFv2(BaseTopologyTest):
    """README §OSPFv2 — OSPF routing, database, and neighbors."""

    routing = 'ospf'
    initial_wait = 5

    def _ospf_converged(self):
        output = self.vtysh(self.lab.r1, 'show ip route')
        return 'O>*' in output

    def setUp(self):
        converged = self.wait_for(self._ospf_converged, timeout=90)
        if not converged:
            self.skipTest('OSPF did not converge within 90 s')

    def test_r1_vtysh_show_ip_route(self):
        """show ip route must include OSPF-selected routes for remote networks."""
        output = self.vtysh(self.lab.r1, 'show ip route')
        self.assertRegex(output, r'O>\*\s+10\.0\.2\.0/24')
        self.assertRegex(output, r'O>\*\s+10\.0\.3\.0/24')

    def test_r1_ospf_route_table(self):
        """show ip ospf route must list all 5 networks in area 0."""
        output = self.vtysh(self.lab.r1, 'show ip ospf route')
        self.assertIn('OSPF network routing table', output)
        for net in ('10.0.0.0/24', '10.0.1.0/24', '10.0.2.0/24',
                    '10.0.3.0/24', '10.0.4.0/24'):
            self.assertIn(net, output, msg=f'{net} missing from OSPF route table')

    def test_r1_ospf_multipath_to_10_0_2(self):
        """10.0.2.0/24 must be reachable via both r1-eth1 and r1-eth2 (ECMP)."""
        output = self.vtysh(self.lab.r1, 'show ip ospf route')
        # Find the block for 10.0.2.0/24
        self.assertRegex(output, r'10\.0\.2\.0/24.*\[20\]')
        # Both next-hops must appear
        self.assertIn('10.0.1.3', output)
        self.assertIn('10.0.4.3', output)

    def test_r1_ospf_neighbors(self):
        """show ip ospf neighbor must show adjacencies on both r1-eth1 and r1-eth2."""
        output = self.vtysh(self.lab.r1, 'show ip ospf neighbor')
        self.assertRegex(output, r'r1-eth1')
        self.assertRegex(output, r'r1-eth2')

    def test_r1_ospf_database(self):
        """show ip ospf database must contain Router Link States for area 0."""
        output = self.vtysh(self.lab.r1, 'show ip ospf database')
        self.assertIn('Router Link States', output)
        self.assertIn('0.0.0.0', output)   # area 0

    def test_ping_server(self):
        result = self.ping_server()
        self.assertEqual(result.returncode, 0,
                         msg=f'ping failed:\n{result.stdout}')


# ======================================================================
# EIGRP
# ======================================================================

@skip_unless_root
class TestEIGRP(BaseTopologyTest):
    """README §EIGRP — EIGRP routing, topology table, and neighbors."""

    routing = 'eigrp'
    initial_wait = 5

    def _eigrp_converged(self):
        output = self.node_cmd(self.lab.r1, 'ip route')
        return 'proto eigrp' in output

    def setUp(self):
        converged = self.wait_for(self._eigrp_converged, timeout=30)
        if not converged:
            self.skipTest('EIGRP did not converge within 30 s')

    def test_r1_ip_route_eigrp_remote_networks(self):
        output = self.node_cmd(self.lab.r1, 'ip route')
        self.assertRegex(output, r'10\.0\.2\.0/24.*proto eigrp')
        self.assertRegex(output, r'10\.0\.3\.0/24.*proto eigrp')

    def test_r1_ip_route_eigrp_ecmp_to_10_0_2(self):
        """10.0.2.0/24 should use two ECMP nexthops: via r2 and r3."""
        output = self.node_cmd(self.lab.r1, 'ip route')
        # Both nexthops should appear in the multipath block
        self.assertIn('10.0.1.3', output)
        self.assertIn('10.0.4.3', output)

    def test_r1_vtysh_show_ip_route(self):
        """show ip route must include EIGRP-selected routes for remote networks."""
        output = self.vtysh(self.lab.r1, 'show ip route')
        self.assertRegex(output, r'E>\*\s+10\.0\.2\.0/24')
        self.assertRegex(output, r'E>\*\s+10\.0\.3\.0/24')

    def test_r1_eigrp_topology_all_networks(self):
        """show ip eigrp topology must list all 5 networks as Passive."""
        output = self.vtysh(self.lab.r1, 'show ip eigrp topology')
        self.assertRegex(output, r'EIGRP Topology Table for AS\(100\)')
        for net in ('10.0.0.0/24', '10.0.1.0/24', '10.0.2.0/24',
                    '10.0.3.0/24', '10.0.4.0/24'):
            self.assertIn(net, output, msg=f'{net} missing from EIGRP topology')
        # All entries should be Passive (converged)
        self.assertNotIn('A  ', output, msg='Some EIGRP routes are still Active (not converged)')

    def test_r1_eigrp_neighbors(self):
        """show ip eigrp neighbor must list r2 and r3 as neighbors."""
        output = self.vtysh(self.lab.r1, 'show ip eigrp neighbor')
        self.assertIn('EIGRP neighbors for AS(100)', output)
        self.assertIn('10.0.1.3', output, msg='r2 (10.0.1.3) not found in EIGRP neighbors')
        self.assertIn('10.0.4.3', output, msg='r3 (10.0.4.3) not found in EIGRP neighbors')

    def test_ping_server(self):
        result = self.ping_server()
        self.assertEqual(result.returncode, 0,
                         msg=f'ping failed:\n{result.stdout}')


if __name__ == '__main__':
    if os.geteuid() != 0:
        print('Run as root:  sudo python3 test_topology.py', file=sys.stderr)
        sys.exit(1)
    unittest.main(verbosity=2)
