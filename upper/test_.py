#!/usr/bin/prego

import glob
from hamcrest import is_not, contains_string
from prego import TestCase, Task, context, terminated
from prego.net import localhost, listen_port
from prego.debian import Package, installed


def wait_clients(clients):
    task = Task('wait clients end')
    for client in clients:
        task.wait_that(client, terminated(), timeout=60)


class UDPTests(TestCase):
    def setUp(self):
        context.port = 2000

    def run_server(self, prog):
        server = Task(detach=True)
        server.assert_that(localhost,
                           is_not(listen_port(context.port, proto='udp')))
        server.command('./{0} $port'.format(prog), timeout=15, expected=None)

        clients = self.run_clients()
        wait_clients(clients)

    def run_clients(self):
        Task().wait_that(localhost, listen_port(context.port, proto='udp'))

        clients = []
        for i in range(10):
            req = 'hello-%s' % i
            client = Task(detach=True)
            client.command('echo %s | ./udp_client.py localhost $port' % req,
                           timeout=15)
            client.assert_that(client.lastcmd.stdout.content,
                               contains_string("Reply is '" + req.upper()))

            clients.append(client)

        return clients

    def test_basic(self):
        self.run_server('udp_server.py')

    def test_fork(self):
        self.run_server('udp_fork.py')

    def test_async(self):
        self.run_server('udp_async_protocol.py')
