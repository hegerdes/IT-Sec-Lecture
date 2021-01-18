#!/usr/bin/python3

import argparse
import sys
import socket
import time
import getpass
import paramiko
import select
import socketserver as SocketServer
from helper.myParser import myParser
from helper.myParser import color as CL


class ForwardServer(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class Default_Handler(SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            chan = self.ssh_transport.open_channel(
                "direct-tcpip",
                (self.chain_host, self.chain_port),
                self.request.getpeername(),
            )
        except Exception as e:
            print(
                "Incoming request to %s:%d failed: %s"
                % (self.chain_host, self.chain_port, repr(e))
            )
            return
        if chan is None:
            print(
                "Incoming request to %s:%d was rejected by the SSH server."
                % (self.chain_host, self.chain_port)
            )
            return

        print(
            "Connected!  Tunnel open %r -> %r -> %r"
            % (
                self.request.getpeername(),
                chan.getpeername(),
                (self.chain_host, self.chain_port),
            )
        )
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)

        peername = self.request.getpeername()
        chan.close()
        self.request.close()
        print("Tunnel closed from %r" % (peername,))


def createSSHClient(conf, user, keyfile):

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.RSAKey.from_private_key_file(keyfile)
    print("*** Connecting...")
    try:
        client.connect(*conf.remote, user, pkey=key)
    except paramiko.PasswordRequiredException:
            print(CL.RED + 'FAILD: Please log in with user and password' + CL.NC)
            password = getpass.getpass(
                "Password for %s@%s: " % (user, conf.remote[0])
            )
            client.connect(*conf.remote, user, password)
    except Exception as e:
        print(CL.RED + 'ConnectionFail; Please check arguments' + CL.NC)

    # Test
    stdin, stdout, stderr = client.exec_command('ls')
    print(stdout.read())

    print('Connected to ssh server {}:{}'.format(conf.remote[0], conf.remote[1]))
    return client


def run_tunnel(conf, transport):
    class SSHHandler(Default_Handler):
        chain_host = conf.dst[0]
        chain_port = conf.dst[1]
        ssh_transport = transport

    with ForwardServer(conf.local, SSHHandler) as server:
        server.serve_forever()


if __name__ == "__main__":

    parser = myParser()
    parser.parser.add_argument('--user', '-u', help='username',default='hegerdes')
    parser.parser.add_argument('--key', '-k', help='ssh key file', default='/home/arthur/.ssh/ITS')
    args = parser.parseArgs()
    conf = parser.parseConfig(args.config_file)[0]

    client = createSSHClient(conf, args.user, args.key)

    run_tunnel(conf, client.get_transport())



