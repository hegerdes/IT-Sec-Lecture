#!/usr/bin/python3

import socket
import struct
import select
import ssl
import os
import time
import signal
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import Config
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST
from helper.ProxyParser import ParseACL
from helper.TmpTestClient import TestClient
from helper.TmpTestClient import TestSocks
from MySOCKS import socks_handler
from BaseProxy import Tunnel


def proxy_serv_handler(context):
    conf = context.server.conf

    # Use SOCKS
    if conf.socks:
        return socks_handler(context)

    use_ssl = True
    try:
        if conf.ssl:
            context.request.do_handshake()
        client_cert = context.request.getpeercert()
        if client_cert:
            CONST.LOGGER.log('ClientCertSubject', CL.GRY,
                  (client_cert['subject'], context.request.version()), CONST.VERBOSE )

        # User not in ACL
        if 'ca' in conf.ssl and not checkACL(conf, client_cert):
            CONST.LOGGER.log('A unautorised user tried to use the Proxy!', CL.RED)
            if client_cert:
                CONST.LOGGER.log('His cert:\n', CL.RED, client_cert['subject'])
            context.request.send(struct.pack('5sb', CONST.PROT_ID,
                                             CONST.BIT_FLAG_MASK['ACL_FAIL_FLAG']))
            context.request.close()
            return
    except ssl.SSLError as e:
        CONST.LOGGER.log('Unothorized connection attampt form {}. Rejected! ErrMsg: {}'
            .format(context.request.getpeername(), e), CL.RED)
        return
    except AttributeError:
        use_ssl = False

    try:
        data = context.request.recv(CONST.REV_BUFFER)
        fixed_header = data[:CONST.FIXED_HEADER]
        dst_data = data[CONST.FIXED_HEADER:]
        prot, conn_flag = struct.unpack('5sb', fixed_header)

        # Check proxy protocol
        if conn_flag != CONST.BIT_FLAG_MASK['CON_Flag'] or prot != CONST.PROT_ID:
            CONST.LOGGER.log('Invalid request. Closing...', CL.RED)
            context.request.sendall(struct.pack(
                '5sb', CONST.PROT_ID, CONST.BIT_FLAG_MASK['PROT_ERR_Flag']))
            raise struct.error('Unkonwn protocol')

        # DST info
        url_length = struct.unpack('I', dst_data[:4])[0]
        url_length, port, url = struct.unpack(
            'IH' + str(url_length) + 's', dst_data[:4 + 2 + url_length])
    except struct.error:
        CONST.LOGGER.log('Request from {}: Proto error! Request rejected!'
            .format(context.request.getpeername()), CL.RED)
        context.request.close()
        return

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as dst_sock:
            dst_sock.connect((url, port))
            CONST.LOGGER.log('Client {} requested {}; SSL={}. Connection to dst: OK'
                .format(context.request.getpeername(), (url, port), use_ssl), CL.BLU)

            context.request.sendall(struct.pack('5sb', CONST.PROT_ID,
                                                CONST.BIT_FLAG_MASK['CON_ACK_Flag']))

            while True:
                #Select example inspired by https://steelkiwi.com/blog/working-tcp-sockets/
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
        CONST.LOGGER.log('Request from {}: Unable to connect to destination: ({},{})\nErrMsg:{}'
            .format(context.request.getpeername(), url, port, e), CL.RED)
        context.request.sendall(struct.pack(
            '5sb', CONST.PROT_ID, CONST.BIT_FLAG_MASK['DST_FAIL_Flag']))
        context.request.close()
        return

    CONST.LOGGER.log('Connection closed from' + str(context.request.getpeername()), CL.GRY)
    context.request.close


def checkACL(conf, cert):
    if conf.acl is None:
        return True

    if cert is None:
        return False

    for subj in cert['subject']:
        for part in subj:
            if 'commonName' in part and part[1] in conf.acl:
                CONST.LOGGER.log('User {} in ACL succesfuly connected!'.format(part[1]), CL.GRN)
                return True
    return False


def checkEnd(data):
    if len(data) > 5 and struct.unpack('5s', data[:5])[0] == CONST.PROT_ID:
        if struct.unpack('b', data[5:6])[0] == CONST.BIT_FLAG_MASK['END_Flag']:
            return True
    return False


# For eval
def TestConfsIperf(host, ports):
    #Set CWD
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    confs = list()
    for i in range(4):
        conf = Config()
        conf.local = {'host': host, 'port': ports[i]}
        confs.append(conf)

    conf1, conf2, conf3, conf4 = confs
    conf2.setSSL({'certificate': 'pki/certificates/server.pem',
                  'key': 'pki/certificates/server.key'})
    conf3.setSSL({'certificate': 'pki/certificates/server.pem',
                  'key': 'pki/certificates/server.key', 'ca': 'pki/certificates/ca.pem'})
    conf4.setSSL({'certificate': 'pki/certificates/server.pem',
                  'key': 'pki/certificates/server.key', 'ca': 'pki/certificates/ca.pem'})
    conf4.acl = ParseACL('conf/acl.txt')

    return (conf1, conf2, conf3, conf4)


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
        if args.ca: ssl_conf['ca'] = args.ca
        conf.setSSL(ssl_conf)

    # Add ACL to config
    if args.acl:
        conf.acl = ParseACL(args.acl)
    if args.socks:
        CONST.LOGGER.log('Using SOCKSv4', CL.BLU)
        conf.socks = True

    servers = []
    try:
        # Iperf-test
        if args.test:
            testports = [6622, 7622, 8622, 9622]
            [CONST.LOGGER.log(conf) for conf in TestConfsIperf(args.host, testports)]
            [servers.append(Tunnel(testconf, proxy_serv_handler, True))
             for testconf in TestConfsIperf(args.host, testports)]
        else:
            servers.append(Tunnel(conf, proxy_serv_handler, True))
        [server.run(True) for server in servers]

        #Pause main thread
        signal.pause()
    except PermissionError as e:
        CONST.LOGGER.log('Permission error. Action not allowed. ErrMSG: ' + str(e), CL.RED)
        exit(0)
    except OSError as e:
        CONST.LOGGER.log('OSError. Probably the port is already used or a filepath is wrong.\nErrMSG: ' + str(e), CL.RED)
        exit(0)
    except KeyboardInterrupt:
        CONST.LOGGER.log('Interruped received. Closing')
        [server.stop() for server in servers]
        exit(0)

    # Testing
    ip, port = ('127.0.0.1', 7622)
    # TestClient(ip, port, "Hello World 1", False)
    # TestClient(ip, port, "Hello World 2")
    # TestClient(ip, port, "Hello World 3")
    # TestSocks(ip, port, destination=("icanhazip.com", 80))
    # time.sleep(10)
