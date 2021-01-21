#!/usr/bin/python3


import sys
import time
import socket
from threading import Thread
import socketserver as SocketServer
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST


class ForwardServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


class Tunnel:
    def __init__(self, conf, handler):
        self.conf = conf
        self.server = ForwardServer(tuple(conf.local.values()), self.Default_Handler)
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


if __name__ == "__main__":
    try:
        parser = ProxyParser()
        configs = parser.parseConfig(parser.parseArgs().config_file)
        proxs = createProxyInstances(configs)
        # proxs = createProxyInstances(parseConfig('FinalExam/config.txt'))

        startProxies(proxs)
        time.sleep(5)
        print('Waited')

    except KeyboardInterrupt:
        print('Interuped received.')
        [proxy.stop() for proxy in proxs]
        print('Exit')
