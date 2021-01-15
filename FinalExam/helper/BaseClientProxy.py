#!/usr/bin/python3

import argparse
import sys
import time
import socket
import threading

# Nice formatting
RED = '\033[1;31m'
GRN = '\033[1;32m'
YEL = '\033[1;33m'
BLU = '\033[1;34m'
GRY = '\033[1;90m'
NC = '\033[0m'  # No Color

PAYLOAD_SIZE = 4096


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
            print(RED + 'Error while opening socket.\nErrMsg: %s' %
                  str(e) + NC + '\nSystem exit')
            exit(0)

    def runClientProxyLoop(self):
        print(GRY + 'Waiting for connections on port ' + str(self.client[1]) + '...' + NC)
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

def parseConfig(config_path):
    configs = list()
    with open(config_path, "r") as fr:
        line = fr.readline()
        while line:
            if line[0] != '#' and len(line) !=1:
                config = list()
                [config.append(part.strip()) for part in line.split(':')]
                if (len(config) != 5): raise ValueError('Illigal length in confogfile: ' + config_path)
                configs.append(config)
            line = fr.readline()
            break   #TODO Remove!!!
    [print(conf) for conf in configs]
    return configs

def createProxyInstances(confs):
    proxies = list()
    [proxies.append(BaseProxyClient(*conf)) for conf in confs]
    return proxies

def startProxies(proxies):
    for proxy in proxies:
        proxy.start()
        break

def versionCheck():
    if sys.version_info<(3,8,0):
        sys.stderr.write("You need python 3.8 or later to run this\n")
        sys.exit(1)

def parseArgs():
    parser = argparse.ArgumentParser(description='Lunches an argparser')
    parser.add_argument('--config-file', '-f', help='Config file')
    return parser.parse_args()


if __name__ == "__main__":
    try:
        versionCheck()
        proxs = createProxyInstances(parseConfig(parseArgs().config_file))
        # proxs = createProxyInstances(parseConfig('FinalExam/config.txt'))

        startProxies(proxs)
        time.sleep(5)
        print('!sdfsdf')

    except KeyboardInterrupt:
        print('Interuped received.')
        [proxy.stop() for proxy in proxs]
        print('Exit')
