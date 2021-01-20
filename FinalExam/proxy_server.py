#!/usr/bin/python3

import socket
import struct
from helper.ProxyParser import ProxyParser
from helper.ProxyParser import Config
from helper.ProxyParser import color as CL
from helper.ProxyParser import constants as CONST
from BaseProxy import Tunnel

example_reqest = 'GET / HTTP/1.1\r\nHost: localhost:8000\r\nConnection: keep-alive\r\nCache-Control: max-age=0\r\nUpgrade-Insecure-Requests: 1\r\nUser-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9\r\nSec-Fetch-Site: none\r\nSec-Fetch-Mode: navigate\r\nSec-Fetch-User: ?1\r\nSec-Fetch-Dest: document\r\nAccept-Encoding: gzip, deflate, br\r\nAccept-Language: en-US,en;q=0.9,de;q=0.8\r\n\r\n'


def proxy_serv_handler(self):
    # TODO Protocoll tx exchange host and loop
    data = self.request.recv(CONST.REV_BUFFER)
    fixed_header = data[:CONST.FIXED_HEADER]
    dst_data = data[CONST.FIXED_HEADER:]
    prot, conn_flag = struct.unpack('5sb', fixed_header)

    if conn_flag != CONST.BIT_FLAG_MASK['CON_Flag'] or prot != CONST.PROT_ID:
        print(CL.RED + 'Invalid request. Closing...' + CL.NC)
        print(len(data.decode()), data)
        self.request.send(struct.pack(
            '5sb', CONST.PROT_ID, CONST.BIT_FLAG_MASK['PROT_ERR_Flag']))
        self.request.close()
        return

    # DST info
    url_length = struct.unpack('I', dst_data[:4])[0]
    url_length, port, url = struct.unpack(
        'IH' + str(url_length) + 's', dst_data[:4 + 2 + url_length])

    # TCP Application reqest data
    client_reqest_data = dst_data[4 + 2 + url_length:]

    client_reqest_data_len = struct.unpack('L', client_reqest_data[:8])[0]
    client_request = struct.unpack(str(
        client_reqest_data_len) + 's', client_reqest_data[8: 8+client_reqest_data_len])[0]

    print('URL_Lenth', url_length, port, url)
    print('client_request', client_request)
    print('Data:', data)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as dst_sock:
        dst_sock.connect((url, port))
        dst_sock.sendall(client_request)
        dst_data = dst_sock.recv(CONST.REV_BUFFER)
        while dst_data:
            self.request.sendall(dst_data)
            dst_data = dst_sock.recv(CONST.REV_BUFFER)

    print('end')
    self.request.send('Echo: '.encode() + data)


def client(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        send = struct.pack('5sb', CONST.PROT_ID,
                           CONST.BIT_FLAG_MASK['CON_Flag'])
        dst_host = 'icanhazip.com'
        dst_port = 80
        dst_payload = struct.pack(
            'IH' + str(len(dst_host)) + 's', len(dst_host), dst_port, dst_host.encode())

        app_payload = struct.pack(
            'L' + str(len(example_reqest)) + 's', len(example_reqest), example_reqest.encode())

        sock.sendall(send + dst_payload + app_payload)
        response = sock.recv(CONST.REV_BUFFER)
        while response:
            print(response)
            response = sock.recv(CONST.REV_BUFFER)


if __name__ == "__main__":

    px_parser = ProxyParser()
    px_parser.parser.add_argument(
        '--host', '-l', help='host name', default='bones.informatik.uni-osnabrueck.de')
    px_parser.parser.add_argument(
        '--port', '-p', help='port to run the proxy server', default=7622)
    args = px_parser.parseArgs()
    conf = Config()
    conf.local = (args.host, args.port)

    tunnel = Tunnel(conf, proxy_serv_handler)
    tunnel.run(False)

    ip, port = ('127.0.0.1', 8000)
    # client(ip, port, "Hello World 1")
    # client(ip, port, "Hello World 2")
    # client(ip, port, "Hello World 3")
