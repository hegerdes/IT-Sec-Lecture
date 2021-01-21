#!/usr/bin/python3

import argparse
import sys
import socket
import time
import getpass
import paramiko
import signal
import select
import socketserver as SocketServer
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST
from BaseProxy import Tunnel


def createSSHClient(conf, user, keyfile, force=False):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    key = paramiko.RSAKey.from_private_key_file(keyfile)

    # Port check
    if conf.remote['port'] != 22 and not force:
        print(CL.YEL + 'Detected a remote port != 22 for a ssh connection.\nOverwirting it to port 22. Use option -F to overwrite this behavior.' + CL.NC)
        conf.remote['port'] = 22

    print("*** Connecting...")
    try:
        client.connect(*tuple(conf.remote.values()), user, pkey=key)
    except paramiko.PasswordRequiredException:
        print(CL.RED + 'FAILD: Please log in with user and password' + CL.NC)
        password = getpass.getpass(
            "Password for %s@%s: " % (user, conf.remote['host']))
        client.connect(*tuple(conf.remote.values()), user, password)
    except Exception as e:
        print(CL.RED + 'ConnectionFail; Please check arguments\n' + CL.NC + str(e))
        raise socket.error('SSH conn fail')

    print('Connected to ssh server {}:{}'.format(
        conf.remote['host'], conf.remote['port']))
    return client


def addServerAtributes(server, transport):
    server.ssh_transport = transport


def ssh_conn_handler(self):
    # https://github.com/paramiko/paramiko/blob/master/demos/forward.py
    try:
        chan = self.server.ssh_transport.open_channel(
            "direct-tcpip",
            (self.server.conf.dst['host'], self.server.conf.dst['port']),
            self.request.getpeername(),
        )
    except Exception as e:
        print('Request to {}:{} failed: {}'.format(
            self.server.conf.dst['host'], self.server.conf.dst['port'], str(e)))
        return
    if chan is None:
        print('Incoming request to {}:{} was rejected.'.format(
            self.server.conf.dst['host'], self.server.conf.dst['port']))
        return

    print(CL.BLU + 'Connected! Tunnel: {} => {} => {}'.format(
        self.request.getpeername(),
        chan.getpeername(),
        (self.server.conf.dst['host'], self.server.conf.dst['port'])), CL.NC)

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
    print(CL.GRY + 'Tunnel closed from', peername, CL.NC)


if __name__ == "__main__":

    try:
        px_parser = ProxyParser()
        px_parser.parser.add_argument(
            '--config-file', '-f', help='Config file', default='conf/config.txt')
        px_parser.parser.add_argument(
            '--force', '-F', action='store_true', default=False)
        px_parser.parser.add_argument(
            '--user', '-u', help='username', default='hegerdes')
        px_parser.parser.add_argument('--key', '-k', help='ssh key file',
                                      default='/home/arthur/.ssh/ITS')  # TODO replace with .ssh/id_rsa
        args = px_parser.parseArgs()

        conf = px_parser.parseConfig(args.config_file)[1]

        # SSH Client
        try:
            client = createSSHClient(conf, args.user, args.key, args.force)
        except socket.error as e:
            print(CL.RED + 'SSHConnection Faild' + CL.NC)
            exit(0)

        # TunnelServer
        try:
            tunnel = Tunnel(conf, ssh_conn_handler)
            addServerAtributes(tunnel.getServer(), client.get_transport())
            tunnel.run(True)
        except PermissionError as e:
            print(CL.RED + 'Permission error. Action not allowed. ErrMSG: ' + str(e) + CL.NC)
            exit(0)
        except OSError as e:
            print(CL.RED + 'OSError. Probably the port is already used. ErrMSG: ' + str(e) + CL.NC)
            exit(0)

        # Put main thread to sleep
        signal.pause()
    except KeyboardInterrupt:
        print('KeybordInterrupt. Shutting down...')
        tunnel.stop()
        client.close()
