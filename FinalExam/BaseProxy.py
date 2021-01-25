#!/usr/bin/python3


import sys
import time
import ssl
import socket
from threading import Thread
import socketserver as SocketServer
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST


class ForwardServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, conf, server_address, RequestHandler, isServer=True, bind_and_activate=True):
        super().__init__(server_address, RequestHandler, False)

        if isServer and conf.ssl and len(conf.ssl) > 0:
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

                # Client auth enabled
                if 'ca' in conf.ssl and conf.ssl['ca']:
                    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                    ctx.verify_mode = ssl.CERT_REQUIRED
                    ctx.load_verify_locations('pki/certificates/ca.pem')
                    print(CL.BLU + 'Using SSL Server & Client auth' + CL.NC, conf.ssl)
                else:
                    print(CL.BLU + 'Using SSL Server auth' + CL.NC, conf.ssl)

                ctx.load_cert_chain(conf.ssl['certificate'], conf.ssl['key'])

                # Wrap the socket
                self.socket = ctx.wrap_socket(self.socket, server_side=True)
            except (FileNotFoundError, TypeError, KeyError) as e:
                print(CL.YEL + 'Cert or key not found. Using Proxy without SSL!' + CL.NC + '\n' + str(e))
        elif isServer:
            print(CL.GRY + 'Not using SSL' + CL.NC)

        if bind_and_activate:
            try:
                self.server_bind()
                self.server_activate()
            except:
                self.server_close()
                raise


class Tunnel:
    def __init__(self, conf, handler, isServer=False):
        self.conf = conf
        self.server = ForwardServer(conf, tuple(conf.local.values()), self.Default_Handler, isServer)
        self.server.myhandler = handler
        self.server.conf = conf
        self.server_thread = None

    class Default_Handler(SocketServer.BaseRequestHandler):
        def handle(self):
            # Forward to custom handler
            return self.server.myhandler(self)

    def run(self, daemon=False):
        self.server_thread = Thread(target=self.server.serve_forever)
        if daemon:
            # Easy exit the server thread with main thread
            self.server_thread.daemon = True
        print((CL.GRN + 'Start listening ({}:{})...' +
               CL.NC).format(self.server.conf.local['host'], self.server.conf.local['port']))
        self.server_thread.start()

    def stop(self):
        if self.server_thread:
            self.server.shutdown()
            self.server_thread.join()

    def getServer(self):
        return self.server

# Old stuff
#
#
class BaseProxyClient (Thread):

    def __init__(self, dst_host, dst_port, proxy_server, proxy_server_port, client_port=5000, client_host='127.0.0.1'):
        super(BaseProxyClient, self).__init__()  # TODO daenon
        self.client = (client_host, int(client_port))
        self.proxy = (proxy_server, int(proxy_server_port))
        self.dst = (dst_host, int(dst_port))

        self.createProxyConnection()
        self.create_listen_socket()

    def run(self):
        self.runClientProxyLoop()

    def stop(self):
        self.c_socket.close()
        self.proxy_conn.close()
        print('closing')
        # self.join()

    def create_listen_socket(self):
        try:
            self.c_socket = socket.socket()
            self.c_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.c_socket.bind(self.client)
            self.c_socket.listen(1)
        except socket.error as e:
            print('Error while opening socket: %s' % str(e))
            exit(0)

    def createProxyConnection(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(self.proxy)
            self.proxy_conn = sock
        except socket.error as e:
            print(CL.RED + 'Error while opening socket.\nErrMsg: %s' %
                  str(e) + CL.NC + '\nSystem exit')
            exit(0)

    def runClientProxyLoop(self):
        print(CL.GRY + 'Waiting for connections on port ' +
              str(self.client[1]) + '...' + CL.NC)
        while True:
            try:
                # New client
                conn, addr = self.c_socket.accept()
                print("Connection from: " + str(addr))

                # Get payload form application-client
                data = conn.recv(CONST.REV_BUFFER)
                while data:
                    # Send to proxy-server
                    self.proxy_conn.sendall(data)
                    # Get answer form proxy-server
                    data = self.proxy_conn.recv(CONST.REV_BUFFER)
                    # Send data to application-client
                    conn.sendall(data)
                    # Wait for new client-application data
                    data = conn.recv(CONST.REV_BUFFER)
                print(str(addr) + " disconnected.")
            except socket.error:
                print('Disconnected form: %s' % str(addr))


def createProxyInstances(confs):
    proxies = list()
    [proxies.append(BaseProxyClient(*conf)) for conf in confs]
    return proxies


def startProxies(proxies):
    for proxy in proxies:
        proxy.start()
        break

