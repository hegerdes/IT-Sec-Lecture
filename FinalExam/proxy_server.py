#!/usr/bin/python3

import socket
import struct
import select
import ssl
import signal
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import Config
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST
from helper.ProxyParser import ParseACL
from MySOCKS import socks_handler
from MySOCKS import TestSocks
from BaseProxy import Tunnel


def proxy_serv_handler(context):
    conf = context.server.conf

    if conf.socks:
        return socks_handler(context)

    use_ssl = True
    try:
        client_cert = context.request.getpeercert()
        if client_cert:
            print(CL.GRY + 'ClientCertSubject' + CL.NC,
                  client_cert['subject'], context.request.version())

        # User not in ACL
        if 'ca' in conf.ssl and not checkACL(conf, client_cert):
            print(CL.RED + 'A unautorised user tried to use the Proxy!' + CL.NC)
            if client_cert:
                print('His cert:\n', client_cert['subject'])
            context.request.send(struct.pack('5sb', CONST.PROT_ID,
                                             CONST.BIT_FLAG_MASK['ACL_FAIL_FLAG']))
            context.request.close()
            return

    except AttributeError:
        use_ssl = False

    data = context.request.recv(CONST.REV_BUFFER)
    fixed_header = data[:CONST.FIXED_HEADER]
    dst_data = data[CONST.FIXED_HEADER:]
    prot, conn_flag = struct.unpack('5sb', fixed_header)

    # Check proxy protocol
    if conn_flag != CONST.BIT_FLAG_MASK['CON_Flag'] or prot != CONST.PROT_ID:
        print(CL.RED + 'Invalid request. Closing...' + CL.NC)
        context.request.sendall(struct.pack(
            '5sb', CONST.PROT_ID, CONST.BIT_FLAG_MASK['PROT_ERR_Flag']))
        context.request.close()
        return

    # DST info
    url_length = struct.unpack('I', dst_data[:4])[0]
    url_length, port, url = struct.unpack(
        'IH' + str(url_length) + 's', dst_data[:4 + 2 + url_length])

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as dst_sock:
            dst_sock.connect((url, port))
            print(CL.BLU + 'client ' + str(context.request.getpeername()) +
                  ' requested ' + str((url, port)) + '. Connection to dst: OK' + CL.NC)

            context.request.sendall(struct.pack('5sb', CONST.PROT_ID,
                                                CONST.BIT_FLAG_MASK['CON_ACK_Flag']))

            while True:
                r, w, x = select.select([context.request, dst_sock], [], [])
                if context.request in r:
                    data = context.request.recv(CONST.REV_BUFFER)
                    if len(data) == 0:
                        break
                    dst_sock.send(data)
                if dst_sock in r:
                    data = dst_sock.recv(CONST.REV_BUFFER)
                    if len(data) != 0:
                        context.request.send(data)

    except socket.error as e:
        print((CL.RED + 'Request from {}: Unable to connect to destination: ({},{})\nErrMsg:{}' +
               CL.NC).format(context.request.getpeername(), url, port, e))
        context.request.sendall(struct.pack(
            '5sb', CONST.PROT_ID, CONST.BIT_FLAG_MASK['DST_FAIL_Flag']))
        context.request.close()
        return

    print(CL.GRY + 'Connection closed from',
          context.request.getpeername(), CL.NC)
    context.request.close


def checkACL(conf, cert):
    if not conf.acl:
        return True

    if cert is None:
        return False

    for subj in cert['subject']:
        for part in subj:
            if 'commonName' in part and part[1] in conf.acl:
                return True
    return False


def checkEnd(data):
    if len(data) > 5 and struct.unpack('5s', data[:5])[0] == CONST.PROT_ID:
        if struct.unpack('b', data[5:6])[0] == CONST.BIT_FLAG_MASK['END_Flag']:
            return True
    return False


def TestClient(ip, port, message, setup_ssl=False):
    if setup_ssl:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.check_hostname = True
        ctx.load_verify_locations("pki/certificates/ca.pem")
        ctx.load_cert_chain('pki/certificates/client1.pem',
                            'pki/certificates/client1.key')

    dst_host = 'icanhazip.com'
    dst_port = 80

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if setup_ssl:
            sock = ctx.wrap_socket(sock, server_hostname='localhost')
        sock.connect((ip, port))
        send = struct.pack('5sb', CONST.PROT_ID,
                           CONST.BIT_FLAG_MASK['CON_Flag'])

        dst_payload = struct.pack(
            'IH' + str(len(dst_host)) + 's', len(dst_host), dst_port, dst_host.encode())
        app_payload = struct.pack(
            'L' + str(len(CONST.EXAMPLE_REQ)) + 's', len(CONST.EXAMPLE_REQ), CONST.EXAMPLE_REQ.encode())

        if setup_ssl:
            print('ServerCert', sock.getpeercert())
        sock.sendall(send + dst_payload + app_payload)
        response = sock.recv(CONST.REV_BUFFER)
        while response:
            print(response)
            sock.send(struct.pack('5sb', CONST.PROT_ID,
                                  CONST.BIT_FLAG_MASK['END_Flag']))
            response = None


if __name__ == "__main__":

    px_parser = ProxyParser()
    px_parser.parser.add_argument(
        '--host', '-l', help='host name', default='bones.informatik.uni-osnabrueck.de')
    px_parser.parser.add_argument(
        '--port', '-p', help='port to run the proxy server', default=7622, type=int)
    px_parser.parser.add_argument(
        '--acl', help='Access Control List-Filepath', default=None)
    px_parser.parser.add_argument(
        '--socks', '-s', help='Use the SOCCKS protocol', action='store_true', default=False)
    args = px_parser.parseArgs()

    # Use config with overwritten options
    conf = Config()
    conf.local = {'host': args.host, 'port': args.port}
    if args.certificate or args.key:
        ssl_conf = {'certificate': args.certificate, 'key': args.key}
        if args.ca:
            ssl_conf['ca'] = args.ca
        conf.setSSL(ssl_conf)

    # Add ACL to config
    if args.acl:
        conf.acl = ParseACL(args.acl)
    if args.socks:
        conf.socks = True

    try:
        tunnel = Tunnel(conf, proxy_serv_handler, True)
        tunnel.run(True)
    except PermissionError as e:
        print(CL.RED + 'Permission error. Action not allowed. ErrMSG: ' + str(e) + CL.NC)
        exit(0)
    except OSError as e:
        print(
            CL.RED + 'OSError. Probably the port is already used. ErrMSG: ' + str(e) + CL.NC)
        exit(0)
    except KeyboardInterrupt:
        print('Interruped received. Closing')
        tunnel.stop()
        exit(0)

    signal.pause()
    # Testing
    ip, port = ('127.0.0.1', 7622)
    # TestClient(ip, port, "Hello World 1", True)
    # TestClient(ip, port, "Hello World 2")
    # TestClient(ip, port, "Hello World 3")
    # TestSocks(ip, port, destination=("icanhazip.com", 80))
