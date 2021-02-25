#!/usr/bin/python3

import socket
import struct
import select
import ssl
import signal
import os
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import Config
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST
from BaseProxy import Tunnel


def proxy_client_handler(context):
    conf = context.server.conf

    use_ssl = True
    try:
        if conf.ssl:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
            ctx.load_verify_locations(conf.ssl['ca'])
            if useClintAuth(conf):
                ctx.load_cert_chain(conf.ssl['certificate'], conf.ssl['key'])
            CONST.LOGGER.log('Using SSL', CL.BLU)
        else:
            use_ssl = False
    except (TypeError, FileNotFoundError, KeyError, ssl.SSLError) as e:
        CONST.LOGGER.log('Err in SSL setup! Check paths.\nNot using SSL. ', CL.YEL, 'ErrMsg: ' + str(e))
        use_ssl = False

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxy_server_sock:
            proxy_server_sock.settimeout(30)

            # SSL wrap
            if use_ssl:
                proxy_server_sock = ctx.wrap_socket(proxy_server_sock, server_hostname=conf.remote['host'])

            CONST.LOGGER.log('Connecting to {}'.format(conf.remote), CL.BLU)
            proxy_server_sock.connect(tuple(conf.remote.values()))

            try:
                CONST.LOGGER.log('ServerCertSubject:\n', CL.GRY,
                    (proxy_server_sock.getpeercert()['subject'], proxy_server_sock.version()), CONST.VERBOSE)
            except AttributeError:
                use_ssl = False

            send = struct.pack('5sb', CONST.PROT_ID,
                               CONST.BIT_FLAG_MASK['CON_Flag'])
            dst_payload = struct.pack(
                'IH' + str(len(conf.dst['host'])) + 's', len(conf.dst['host']), conf.dst['port'], conf.dst['host'].encode())

            proxy_server_sock.sendall(send + dst_payload)
            data = proxy_server_sock.recv(CONST.REV_BUFFER)

            if not data or len(data) < 6:
                raise struct.error('Invalid response')

            prot, status = struct.unpack('5sb', data[:6])
            if status != CONST.BIT_FLAG_MASK['CON_ACK_Flag']:
                if status == CONST.BIT_FLAG_MASK['DST_FAIL_Flag']:
                    CONST.LOGGER.log('Destination not reachable. Closing Socket', CL.RED)
                    context.request.send(b'Destination not reachable')
                proxy_server_sock.close()
                context.request.close()
                CONST.LOGGER.log('Protocol ERROR. Closing', CL.RED)
                return

            CONST.LOGGER.log('Connected! Tunnel: {} => {} => {}'.format(
                context.request.getpeername(),
                proxy_server_sock.getpeername(),
                (context.server.conf.dst['host'], context.server.conf.dst['port'])), CL.GRN)

            while True:
                # Select example inspired by https://steelkiwi.com/blog/working-tcp-sockets/
                r, w, x = select.select([context.request, proxy_server_sock], [], [])
                if context.request in r:
                    data = context.request.recv(CONST.REV_BUFFER)
                    if len(data) == 0:
                        break
                    proxy_server_sock.send(data)
                if proxy_server_sock in r:
                    data = proxy_server_sock.recv(CONST.REV_BUFFER)
                    if len(data) == 0:
                        pass
                    if len(data) != 0:
                        context.request.send(data)

            # Send End_Flag and autoclose socket
            proxy_server_sock.send(struct.pack(
                '5sb', CONST.PROT_ID, CONST.BIT_FLAG_MASK['END_Flag']))

    except struct.error:
        CONST.LOGGER.log('Protocol error! Proibly a SSL related handshake fail', CL.RED)
    except ssl.SSLError as e:
        CONST.LOGGER.log('Server dinied access. Error in SSL communication. Make sure both systems use SSL and certs are valid!', CL.   RED, '\nErrMsg: ' + str(e))
        context.request.send(b'ProxyServerAccsessDinied')
        context.request.close()
        CONST.LOGGER.log('Tunnel closed' + CL.GRY)
        return
    except TimeoutError as e:
        CONST.LOGGER.log('Timeout! ProxyServer did not answer.', CL.RED, '\nErrMsg: ' + str(e))
        context.request.send(b'ProxyServerTimeout')
        context.close()
    except socket.error as e:
        CONST.LOGGER.log('Unable to connect to proxy. Err: ' + str(e), CL.RED)
        context.request.close()
        return
    CONST.LOGGER.log('Tunnel closed from ' + str(context.request.getpeername()), CL.GRY)


def useClintAuth(conf):
    return 'certificate' in conf.ssl and conf.ssl['certificate'] and 'key' in conf.ssl and conf.ssl['key']


# Iperf-eval settings
def TestConfsIperf(confs):
    # Set CWD
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    confs[1].setSSL({'ca': 'pki/certificates/ca.pem'})
    confs[2].setSSL({'certificate': 'pki/certificates/client1.pem',
                     'key': 'pki/certificates/client1.key', 'ca': 'pki/certificates/ca.pem'})
    confs[3].setSSL({'certificate': 'pki/certificates/client1.pem',
                     'key': 'pki/certificates/client1.key', 'ca': 'pki/certificates/ca.pem'})

    return confs


if __name__ == "__main__":
    try:
        px_parser = ProxyParser()
        px_parser.parser.add_argument(
            '--config-file', '-f', help='Config file', default='conf/config.txt')
        args = px_parser.parseArgs()

        confs = px_parser.parseConfig()
        px_parser.setSSLConf()
        tunnels = []

        # Iperf eval
        if args.test:
            confs = TestConfsIperf(confs)
        if CONST.VERBOSE:
            [CONST.LOGGER.log(conf) for conf in confs]

        [tunnels.append(Tunnel(conf, proxy_client_handler)) for conf in confs]
        [tunnel.run(True) for tunnel in tunnels]

        # Pause main thread
        signal.pause()
    except OSError as e:
        CONST.LOGGER.log('Coud not start one ore more ProxyClients. Make sure the config exists, valid and every Client has its own free port!', CL.RED, '\nErrMsg: ' + str(e))
        exit(0)
    except KeyboardInterrupt:
        CONST.LOGGER.log('Interruped received. Closing')
        [tunnel.stop() for tunnel in tunnels]
