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

    def __init__(self, conf, server_address, RequestHandler, isServer=False, bind_and_activate=True):
        # Super constructor without bind to allow changes to the socket
        super().__init__(server_address, RequestHandler, False)

        #Just serverside stuff
        if isServer and conf.ssl and len(conf.ssl) > 0:
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

                # Client auth enabled
                if 'ca' in conf.ssl and conf.ssl['ca']:
                    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                    ctx.verify_mode = ssl.CERT_REQUIRED
                    ctx.load_verify_locations('pki/certificates/ca.pem')
                    CONST.LOGGER.log('Using SSL Server & Client auth', CL.BLU, conf.ssl, CONST.VERBOSE)
                else:
                    CONST.LOGGER.log('Using SSL Server auth', CL.BLU, conf.ssl, CONST.VERBOSE)

                ctx.load_cert_chain(conf.ssl['certificate'], conf.ssl['key'])

                # Wrap the socket
                self.socket = ctx.wrap_socket(self.socket, server_side=True, do_handshake_on_connect=False)
            except (FileNotFoundError, TypeError, KeyError) as e:
                CONST.LOGGER.log('Cert or key not found. Using Proxy without SSL!', CL.YEL, str(e))
        elif isServer:
            CONST.LOGGER.log('Not using SSL', CL.GRY)

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
        CONST.LOGGER.log('Start listening ({}:{})...'.format(self.server.conf.local['host'], self.server.conf.local['port']), CL.GRN)
        self.server_thread.start()

    def stop(self):
        if self.server_thread:
            self.server.shutdown()
            self.server_thread.join()
        else:
            self.server.shutdown()

    def getServer(self):
        return self.server
