#!/usr/bin/python3

import socket
import struct
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import Config
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST
from BaseProxy import Tunnel


def proxy_client_handler(self):
    conf = self.server.conf
    data = self.request.recv(CONST.REV_BUFFER)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxy_server_sock:
        proxy_server_sock.connect(conf.remote)
        send = struct.pack('5sb', CONST.PROT_ID,
                           CONST.BIT_FLAG_MASK['CON_Flag'])
        dst_payload = struct.pack(
            'IH' + str(len(conf.dst[0])) + 's', len(conf.dst[0]), conf.dst[1], conf.dst[0].encode())

        app_payload = struct.pack(
            'L' + str(len(data.decode())) + 's', len(data.decode()), data)

        proxy_server_sock.sendall(send + dst_payload + app_payload)
        response = proxy_server_sock.recv(CONST.REV_BUFFER)

        print('Connected! Tunnel: {} => {} => {}'.format(
            self.request.getpeername(),
            proxy_server_sock.getpeername(),
            (self.server.conf.dst[0], self.server.conf.dst[1])))

        if response == b'YPROX`':
            print(CL.RED + 'Protocoll error! ProxyServer rejeted this request' + CL.NC)
            proxy_server_sock.close()
            self.request.close()
            return

        while response:
            self.request.send(response)
            response = proxy_server_sock.recv(CONST.REV_BUFFER)

    print('Tunnel closed from', self.request.getpeername())



if __name__ == "__main__":
    px_parser = ProxyParser()
    px_parser.parser.add_argument(
        '--config-file', '-f', help='Config file', default='conf/config.txt')
    args = px_parser.parseArgs()

    conf = px_parser.parseConfig(args.config_file)[2]

    tunnel = Tunnel(conf, proxy_client_handler)
    tunnel.run()
