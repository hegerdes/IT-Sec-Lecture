#!/usr/bin/python3

import socket
import select
import struct

from helper.ProxyParser import constants as CONST
from helper.ProxyParser import color as CL


def socks_handler(context):
    data = context.request.recv(CONST.REV_BUFFER)
    protInfo1 = getProtInfo(data)
    vn, cn, port, ip1, ip2, ip3, ip4 = protInfo1
    assert vn == CONST.SOCKS_VERSION

    if cn != 1 and vn != 2:
        # Bind is handeld by the SocketServer TCP
        CONST.LOGGER.log('Unsuported SOCKS request', CL.RED)
        context.request.send(struct.pack(
            '!BBHBBBB', 0, 91, port, ip1, ip2, ip3, ip4))
        return

    # requestet a bind. But we are alrady have a bind listinimg SOCKS server.
    # So send this socket address
    if cn == 2:
        context.request.send(struct.pack('!BBHBBBB', 0, 90, 0, 0, 0, 0, 0))
        protInfo2 = getProtInfo(context.request.recv(CONST.REV_BUFFER))

        if not equalDST(protInfo1, protInfo2):
            context.request.send(struct.pack(
                '!BBHBBBB', 0, 91, port, ip1, ip2, ip3, ip4))
            return

    if isHost((ip1, ip2, ip3, ip4)):
        length = len(data) - 9 - 1
        address = struct.unpack('!' + str(length) + 's',
                                data[9: len(data) - 1])[0]
    else:
        address = socket.inet_ntoa(data[4:8])
    CONST.LOGGER.log('{} requestet {}:{}'.format(context.request.getpeername(), address, port),
        CL.BLU)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as dst_socket:
            dst_socket.settimeout(120)
            dst_socket.connect((address, port))
            tmp = list()
            [tmp.append(int(ip_int))
             for ip_int in dst_socket.getpeername()[0].split('.')]
            ip1, ip2, ip3, ip4 = tmp
            context.request.send(struct.pack(
                '!BBHBBBB', 0, 90, port, ip1, ip2, ip3, ip4))

            while True:
                r, w, x = select.select([context.request, dst_socket], [], [])
                if context.request in r:
                    data = context.request.recv(CONST.REV_BUFFER)
                    if len(data) == 0:
                        break
                    dst_socket.send(data)
                if dst_socket in r:
                    data = dst_socket.recv(CONST.REV_BUFFER)
                    if len(data) == 0:
                        break
                    context.request.send(data)
    except socket.error as e:
        context.request.send(struct.pack(
            '!BBHBBBB', 0, 92, port, ip1, ip2, ip3, ip4))
        CONST.LOGGER.log('Error in the dst connection!', CL.RED, '\nErrMSG: ' + str(e))


def getProtInfo(data):
    if len(data) < 9:
        CONST.LOGGER.log('Error! Not enough data', CL.RED)
        return None

    return struct.unpack('!BBHBBBB', data[:8])


def equalDST(info1, info2):
    isEqual = True
    for i in range(2, 7):
        if info1[i] != info2[i]:
            isEqual = False
    return isEqual


def TestSocks(host, port, destination=("icanhazip.com", 80)):
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


def isHost(ip):
    if ip[0] == 0 and ip[1] == 0 and ip[2] == 0 and ip[3] != 0:
        return True
    return False
