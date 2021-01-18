#!/usr/bin/python3


import sys
import time
import socket
import threading
import socketserver as SocketServer
from helper.myParser import myParser
from helper.myParser import color as CL

PAYLOAD_SIZE = 4096

class ForwardServer(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class Tunnel:

    def __init__(self, conf, handler):
        self.conf = conf
        self.server = ForwardServer(conf.local, self.Default_Handler)
        self.server.myhandler = handler
        self.server.conf = conf

    class Default_Handler(SocketServer.BaseRequestHandler):
        def handle(self):
            return self.server.myhandler(self)

    def run(self):
        self.server.serve_forever()

    def getServer(self):
        return self.server



class BaseProxyClient (threading.Thread):

    def __init__(self, dst_host, dst_port, proxy_server, proxy_server_port, client_port=5000, client_host='127.0.0.1'):
        super(BaseProxyClient,self).__init__() #TODO daenon
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
        print(CL.GRY + 'Waiting for connections on port ' + str(self.client[1]) + '...' + CL.NC)
        while True:
            try:
                # New client
                conn, addr = self.c_socket.accept()
                print("Connection from: " + str(addr))

                # Get payload form application-client
                data = conn.recv(PAYLOAD_SIZE)
                while data:
                    # Send to proxy-server
                    self.proxy_conn.sendall(data)
                    # Get answer form proxy-server
                    data = self.proxy_conn.recv(PAYLOAD_SIZE)
                    # Send data to application-client
                    conn.sendall(data)
                    # Wait for new client-application data
                    data = conn.recv(PAYLOAD_SIZE)
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
        parser = myParser()
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
