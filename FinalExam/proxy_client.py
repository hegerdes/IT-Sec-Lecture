#!/usr/bin/python3

import socket
import struct
import select
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import Config
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST
from BaseProxy import Tunnel


def proxy_client_handler(self):
    conf = self.server.conf

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxy_server_sock:
            print((CL.BLU + 'Connecting to {}' + CL.NC).format(conf.remote))
            proxy_server_sock.connect(tuple(conf.remote.values()))
            send = struct.pack('5sb', CONST.PROT_ID,
                               CONST.BIT_FLAG_MASK['CON_Flag'])
            dst_payload = struct.pack(
                'IH' + str(len(conf.dst['host'])) + 's', len(conf.dst['host']), conf.dst['port'], conf.dst['host'].encode())

            proxy_server_sock.sendall(send + dst_payload)
            data = proxy_server_sock.recv(CONST.REV_BUFFER)

            if not data or len(data) < 6:
                print('empty or invalid')

            prot, status = struct.unpack('5sb', data[:6])
            if status != CONST.BIT_FLAG_MASK['CON_ACK_Flag']:
                print('Prot ERR')

            print(CL.GRN + 'Connected! Tunnel: {} => {} => {}'.format(
                self.request.getpeername(),
                proxy_server_sock.getpeername(),
                (self.server.conf.dst['host'], self.server.conf.dst['port'])) + CL.NC)

            while True:
                r, w, x = select.select(
                    [self.request, proxy_server_sock], [], [])
                if self.request in r:
                    data = self.request.recv(CONST.REV_BUFFER)
                    if len(data) == 0:
                        break
                    proxy_server_sock.send(data)
                if proxy_server_sock in r:
                    data = proxy_server_sock.recv(CONST.REV_BUFFER)
                    if len(data) == 0:
                        break
                    self.request.send(data)

    except socket.error as e:
        print(CL.RED + 'Unable to connect to proxy. Err: ' + str(e) + CL.NC)
        return
    print(CL.GRY + 'Tunnel closed from', self.request.getpeername(), CL.NC)


def handleErr(client, proxy, msg=b'proxy responded with an error'):
    proxy.close()
    client.sendall(msg)
    client.close()
    return


def errCheck(response):
    if response and len(response) >= 6:
        # print(response)
        prot, status = struct.unpack('5sb', response[:6])
        if prot == CONST.PROT_ID:
            if status == CONST.BIT_FLAG_MASK['PROT_ERR_Flag']:
                print(
                    CL.RED + 'Protocoll error! ProxyServer rejeted this request' + CL.NC)
                return True
            if status == CONST.BIT_FLAG_MASK['DST_FAIL_Flag']:
                print(
                    CL.RED + 'Connection error! ProxyServer can\'t reach the destination server: ' + str(conf.dst) + CL.NC)
                return True
            if status == CONST.BIT_FLAG_MASK['END_Flag']:
                print(
                    CL.RED + 'Proxy closed connection! Proxy:' + str(conf.dst) + CL.NC)
                return True
    else:
        return False


if __name__ == "__main__":
    px_parser = ProxyParser()
    px_parser.parser.add_argument(
        '--config-file', '-f', help='Config file', default='conf/config.txt')
    px_parser.parser.add_argument('--ca', '-C', help='CA certificate path', default=None)
    args = px_parser.parseArgs()

    confs = px_parser.parseConfig()
    px_parser.setSSLConf()


    tunnel = Tunnel(confs[3], proxy_client_handler)
    tunnel.run()
    # tunnel1 = Tunnel(confs[1], proxy_client_handler)
    # tunnel1.run()
