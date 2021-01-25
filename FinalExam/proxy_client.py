#!/usr/bin/python3

import socket
import struct
import select
import ssl
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import Config
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST
from BaseProxy import Tunnel


def proxy_client_handler(self):
    conf = self.server.conf

    use_ssl = True
    try:
        if conf.ssl:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
            ctx.load_verify_locations(conf.ssl['ca'])
            ctx.load_cert_chain(conf.ssl['certificate'], conf.ssl['key'])
            print(CL.BLU + 'Using SSL' + CL.NC)
        else:
            use_ssl = False
    except (TypeError, FileNotFoundError, KeyError) as e:
        print(CL.YEL + 'Err in SSL setup!\n Not using SSL' + CL.NC + '\nErr:', e)
        use_ssl = False

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxy_server_sock:

            # SSL wrap
            if use_ssl:
                proxy_server_sock = ctx.wrap_socket(
                    proxy_server_sock, server_hostname=conf.remote['host'])

            print((CL.BLU + 'Connecting to {}' + CL.NC).format(conf.remote))
            proxy_server_sock.connect(tuple(conf.remote.values()))

            try:
                print(CL.GRY + 'ServerCertSubject:\n', CL.NC,
                      proxy_server_sock.getpeercert()['subject'], proxy_server_sock.version())
            except AttributeError:
                use_ssl = False

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
                if status == CONST.BIT_FLAG_MASK['DST_FAIL_Flag']:
                    print(CL.RED + 'Destination not reachable. Closing Socket' + CL.NC)
                    self.request.send(b'Destination not reachable')
                proxy_server_sock.close()
                self.request.close()
                print(CL.RED + 'Protocol ERROR. Closing' + CL.NC)
                return

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
                        pass
                    if len(data) != 0:
                        self.request.send(data)

            # Send End_Flag and autoclose socket
            proxy_server_sock.send(struct.pack(
                '5sb', CONST.PROT_ID, CONST.BIT_FLAG_MASK['END_Flag']))

    except ssl.SSLError as e:
        print(CL.RED + 'Server dinied access. Error in SSL communication. Make sure both systems use SSL and certs are valid!' +
              CL.NC + '\nErrMsg: ' + str(e))
        self.request.close()
        return
    except socket.error as e:
        print(CL.RED + 'Unable to connect to proxy. Err: ' + str(e) + CL.NC)
        self.request.close()
        return
    print(CL.GRY + 'Tunnel closed from', self.request.getpeername(), CL.NC)


if __name__ == "__main__":
    px_parser = ProxyParser()
    px_parser.parser.add_argument(
        '--config-file', '-f', help='Config file', default='conf/config.txt')
    args = px_parser.parseArgs()

    confs = px_parser.parseConfig()
    px_parser.setSSLConf()
    [print(conf) for conf in confs]

    tunnel = Tunnel(confs[3], proxy_client_handler)
    tunnel.run()
    # tunnel1 = Tunnel(confs[1], proxy_client_handler)
    # tunnel1.run()
