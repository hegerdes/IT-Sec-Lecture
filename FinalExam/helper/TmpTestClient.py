#!/usr/bin/python3

import ssl
import socket
import struct

class constants:
    REV_BUFFER = 4096
    VERBOSE = True
    LOGGER = None
    SOCKS_VERSION = 4

    PROT_ID = b'YPROX'
    FIXED_HEADER = 6
    BIT_FLAG_MASK = {
        'CON_Flag':             0b00000000,
        'CON_ACK_Flag':         0b00000001,
        'DST_FAIL_Flag':        0b01000000,
        'LOC_FAIL_Flag':        0b11000000,
        'END_Flag':             0b00100000,
        'RPL_RADY_Flag':        0b10100000,
        'PROT_ERR_Flag':        0b01100000,
        'ACL_FAIL_FLAG':        0b00000010,
        'SSL_FAIL_FLAG':        0b00000011,
    }

    EXAMPLE_REQ = 'GET / HTTP/1.1\r\nHost: sys.cs.uos.de:80\r\nConnection: keep-alive\r\nCache-Control: max-age=0\r\nUpgrade-Insecure-Requests: 1\r\nUser-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9\r\nSec-Fetch-Site: none\r\nSec-Fetch-Mode: navigate\r\nSec-Fetch-User: ?1\r\nSec-Fetch-Dest: document\r\nAccept-Encoding: gzip, deflate, br\r\nAccept-Language: en-US,en;q=0.9,de;q=0.8\r\n\r\n'


def TestClient(ip, port, message, setup_ssl=False):
    CONST = constants
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

        if setup_ssl:
            print('ServerCert', sock.getpeercert())

        send = struct.pack('5sb', CONST.PROT_ID, CONST.BIT_FLAG_MASK['CON_Flag'])
        dst_payload = struct.pack(
            'IH' + str(len(dst_host)) + 's', len(dst_host), dst_port, dst_host.encode())
        app_payload = struct.pack(
            'L' + str(len(CONST.EXAMPLE_REQ)) + 's', len(CONST.EXAMPLE_REQ), CONST.EXAMPLE_REQ.encode())

        sock.sendall(send + dst_payload)
        response = sock.recv(CONST.REV_BUFFER)
        while response:
            print(response)
            sock.send(struct.pack('5sb', CONST.PROT_ID, CONST.BIT_FLAG_MASK['END_Flag']))
            response = None

def TestSocks(host, port, destination=("icanhazip.com", 80)):
    CONST = constants
    import socks

    s = socks.socksocket()  # Same API as socket.socket in the standard lib

    s.set_proxy(socks.SOCKS4, host, port)
    s.connect(destination)
    s.sendall(CONST.EXAMPLE_REQ.encode())
    response = s.recv(CONST.REV_BUFFER)
    while response:
        print(response)
        s.send(struct.pack('5sb', CONST.PROT_ID,
                           CONST.BIT_FLAG_MASK['END_Flag']))
        response = None
