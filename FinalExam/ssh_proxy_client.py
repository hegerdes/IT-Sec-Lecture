#!/usr/bin/python3

import argparse
import sys
import socket
import time
import getpass
import paramiko
import select
import socketserver as SocketServer
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST
from BaseProxy import Tunnel


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
            "Password for %s@%s: " % (user, conf.remote[0]))
        client.connect(*conf.remote, user, password)
    except Exception as e:
        print(CL.RED + 'ConnectionFail; Please check arguments' + CL.NC)

    print('Connected to ssh server {}:{}'.format(conf.remote[0], conf.remote[1]))
    return client

def addServerAtributes(server, transport):
    server.ssh_transport = transport

def ssh_conn_handler(self):
    # https://github.com/paramiko/paramiko/blob/master/demos/forward.py
    try:
        chan = self.server.ssh_transport.open_channel(
            "direct-tcpip",
            (self.server.conf.dst[0], self.server.conf.dst[1]),
            self.request.getpeername(),
        )
    except Exception as e:
        print('Request to {}:{} failed: {}'.format(
            self.server.conf.dst[0], self.server.conf.dst[1], str(e)))
        return
    if chan is None:
        print('Incoming request to {}:{} was rejected.'.format(
            self.server.conf.dst[0], self.server.conf.dst[1]))
        return

    print('Connected! Tunnel: {} => {} => {}'.format(
        self.request.getpeername(),
        chan.getpeername(),
        (self.server.conf.dst[0], self.server.conf.dst[1])))

    while True:
        r, w, x = select.select([self.request, chan], [], [])
        if self.request in r:
            data = self.request.recv(CONST.REV_BUFFER)
            if len(data) == 0:
                break
            chan.send(data)
        if chan in r:
            data = chan.recv(CONST.REV_BUFFER)
            if len(data) == 0:
                break
            self.request.send(data)

    peername = self.request.getpeername()
    chan.close()
    self.request.close()
    print('Tunnel closed from', peername)


if __name__ == "__main__":

    px_parser = ProxyParser()
    px_parser.parser.add_argument('--config-file', '-f', help='Config file', default='conf/config.txt')
    px_parser.parser.add_argument(
        '--user', '-u', help='username', default='hegerdes')
    px_parser.parser.add_argument('--key', '-k', help='ssh key file',
                               default='/home/arthur/.ssh/ITS')  # TODO replace with .ssh/id_rsa
    args = px_parser.parseArgs()

    conf = px_parser.parseConfig(args.config_file)[1]

    client = createSSHClient(conf, args.user, args.key)

    tunnel = Tunnel(conf, ssh_conn_handler)
    addServerAtributes(tunnel.getServer(), client.get_transport())
    tunnel.run()
