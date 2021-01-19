#!/usr/bin/python3

import socket
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import Config
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST
from BaseProxy import Tunnel


def proxy_serv_handler(self):
    #TODO Protocoll tx exchange host and loop
    data = self.request.recv(CONST.REV_BUFFER)
    print(data)
    self.request.send('Echo: '.encode() + data)



def client(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        sock.sendall(b'Hello World')
        response = str(sock.recv(CONST.REV_BUFFER).decode())
        print("Received: {}".format(response))


if __name__ == "__main__":

    px_parser = ProxyParser()
    px_parser.parser.add_argument(
        '--host', '-l', help='host name', default='127.0.0.1')
    px_parser.parser.add_argument(
        '--port', '-p', help='port to run the proxy server', default=8000)
    args = px_parser.parseArgs()
    conf = Config()
    conf.local = (args.host, args.port)

    tunnel = Tunnel(conf, proxy_serv_handler)
    tunnel.run(False)

    ip, port = ('127.0.0.1', 8000)
    client(ip, port, "Hello World 1")
    client(ip, port, "Hello World 2")
    client(ip, port, "Hello World 3")
