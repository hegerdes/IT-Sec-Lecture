#!/usr/bin/python3

import argparse
import sys
import os
import socket
import time
import getpass
import paramiko
import signal
import select
import subprocess
import socketserver as SocketServer
from threading import Thread
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST
from BaseProxy import Tunnel

# Solutions with subprocess
class SubProcessTunnel(Thread):

    def __init__(self, conf, user, force):
        Thread.__init__(self)
        checkDstPort(conf, force)
        self.ps = None
        self.output = None
        self.cmd = 'ssh -L 127.0.0.1:{}:{}:{} {}@{} -p {} -N'.format(
            conf.local['port'], conf.dst['host'], conf.dst['port'], user, conf.remote['host'], conf.remote['port'])

    def run(self):
        try:
            CONST.LOGGER.log('Executing: ' + self.cmd, CL.GRN)
            self.ps = subprocess.Popen(
                self.cmd, shell=True, stdout=subprocess.STDOUT, stderr=subprocess.STDOUT)
            self.ps.wait()
            # self.output = self.ps.communicate()

        except Exception as e:
            CONST.LOGGER.log('Stopping SSH-Tunnel:' + str(e), CL.RED)
            raise socket.error('SSHTunnelFail')

    def stop(self):
        CONST.LOGGER.log('Stopping process', CL.GRY)
        self.ps.kill()

# Solution with paramiko. More elegant though
def createSSHClient(conf, user, keyfile, force=False):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    key = paramiko.RSAKey.from_private_key_file(keyfile)

    # Port check for ssh dst
    checkDstPort(conf, force)

    CONST.LOGGER.log("*** Connecting SSHTunnel...", CL.GRN)
    try:
        client.connect(*tuple(conf.remote.values()), user, pkey=key)
    except paramiko.PasswordRequiredException:
        CONST.LOGGER.log('FAILD: Please log in with user and password', CL.RED)
        password = getpass.getpass(
            "Password for %s@%s: " % (user, conf.remote['host']))
        client.connect(*tuple(conf.remote.values()), user, password)
    except Exception as e:
        CONST.LOGGER.log('ConnectionFail; Please check arguments\n', CL.RED, str(e))
        raise socket.error('SSH conn fail')

    CONST.LOGGER.log('Connected to ssh server {}:{}'.format(
        conf.remote['host'], conf.remote['port']))
    return client


def ssh_conn_handler(context):
    peername = context.request.getpeername()

    try:
        # New channel for connection
        chan = context.server.ssh_transport.open_channel(
            "direct-tcpip",
            (context.server.conf.dst['host'], context.server.conf.dst['port']),
            peername)
    except Exception as e:
        CONST.LOGGER.log('Request to {}:{} failed: {}'.format(
            context.server.conf.dst['host'], context.server.conf.dst['port'], str(e)), CL.RED)
        context.request.send(b'Coud not connect to dest')
        return
    if chan is None:
        CONST.LOGGER.log('Request to {}:{} was rejected.'.format(
            context.server.conf.dst['host'], context.server.conf.dst['port']), CL.RED)
        return

    CONST.LOGGER.log('Connected! Tunnel: {} => {} => {}'.format(peername,
        chan.getpeername(), (context.server.conf.dst['host'], context.server.conf.dst['port'])))

    while True:
        #Select example inspired by https://steelkiwi.com/blog/working-tcp-sockets/
        r, w, x = select.select([context.request, chan], [], [])
        if context.request in r:
            data = context.request.recv(CONST.REV_BUFFER)
            if len(data) == 0:
                break
            chan.send(data)
        if chan in r:
            data = chan.recv(CONST.REV_BUFFER)
            if len(data) == 0:
                break
            context.request.send(data)

    chan.close()
    context.request.close()
    CONST.LOGGER.log('Tunnel closed from' + str(peername), CL.GRY)


def addServerAtributes(server, transport):
    server.ssh_transport = transport


def checkDstPort(conf, force):
    if conf.remote['port'] != 22 and not force:
        CONST.LOGGER.log('Detected a remote port != 22 for a ssh connection.\nOverwirting it to port 22. Use option -F to overwrite this behavior.', CL.YEL)
        conf.remote['port'] = 22


if __name__ == "__main__":

    try:
        px_parser = ProxyParser()
        px_parser.parser.add_argument(
            '--config-file', '-f', help='Config file', default='conf/config.txt')
        px_parser.parser.add_argument(
            '--force', '-F', action='store_true', default=False)
        px_parser.parser.add_argument(
            '--use-subprocess', '-s', action='store_true', default=False)
        px_parser.parser.add_argument(
            '--user', '-u', help='username', default='hegerdes') # TODO replace with os.getlogin()
        px_parser.parser.add_argument('--ssh-key', '-K', help='ssh key file',
            default=os.path.join(os.environ['HOME'], '.ssh', 'ITS'))  # TODO replace with .ssh/id_rsa

        args = px_parser.parseArgs()
        confs = px_parser.parseConfig()
        [CONST.LOGGER.log(conf, print_to_console=CONST.VERBOSE) for conf in confs]

        if args.certificate or args.key or args.ca or args.test:
            CONST.LOGGER.log('Certs, Cert-keys, CA and testMode are mot supported by this modul. Ignoring options!' + CL.YEL)

        connections = []
        if args.use_subprocess:
            # Use subprocess
            [connections.append(SubProcessTunnel(conf, args.user, args.force)) for conf in confs]
            [conn.start() for conn in connections]

        else:
            # SSH Client
            # Use paramiko ssh-lib.
            # Shares ONE ssh connection between all client instances
            try:
                client = createSSHClient(confs[0], args.user, args.ssh_key, args.force)
            except socket.error as e:
                CONST.LOGGER.log('SSHConnection Faild', CL.RED)
                exit(0)

            # TunnelServer
            try:
                for conf in confs:
                    tunnel = Tunnel(conf, ssh_conn_handler)
                    addServerAtributes(tunnel.getServer(), client.get_transport())
                    tunnel.run(True)
                    connections.append(tunnel)
            except PermissionError as e:
                CONST.LOGGER.log('Permission error. Action not allowed. ErrMSG: ' + str(e), CL.RED)
                exit(0)
            except OSError as e:
                CONST.LOGGER.log('OSError. Probably the port is already used. ErrMSG: ' + str(e), CL.RED)
                exit(0)

            # Put main thread to sleep
            signal.pause()
    except socket.error:
        CONST.LOGGER.log('Comminication error. Please check settings!', CL.RED)
        exit(0)
    except KeyboardInterrupt:
        CONST.LOGGER.log('KeybordInterrupt. Shutting down...')
        if args.use_subprocess:
            [conn.stop() for conn in connections]
            [conn.join() for conn in connections]
        else:
            [conn.stop() for conn in connections]
            client.close()
