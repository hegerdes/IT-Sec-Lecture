import socket


class RawSocket:
    '''
        This Class creates a raw socket which can be used to send and receive
        bytes. Note that this is NOT a TCP or UDP socket. You can send any kind
        of packet types from the AF_INET-Family. Also, Port-Numbers don't apply
        to a raw socket. Though, the socket is configured to receive only TCP
        packets from the kernel. As Port-Numbers don't apply, you'll get
        any kind of TCP traffic with an included IPv4-Header. This means, you
        might receive your own packets aswell :).
    '''

    def __init__(self, addr, timeout=0):
        '''
            Initialize the socket

            Arguments:
                addr -- the IPv4 address to use and bind to (e.g. "127.0.0.1")

            Keyword Arguments:
                timeout -- the recv timeout
        '''
        assert isinstance(timeout, int) and timeout >= 0

        # create the raw socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                   socket.IPPROTO_TCP)

        # set socket options
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

        # bind to 0 to kick off some kernel-internal functions
        self._sock.bind((addr, 0))

        # set timeout
        if timeout != 0:
            self._sock.settimeout(timeout)

        self._addr = addr

    def send(self, ipv4packetbytes):
        '''
            Send a SimpleIPv4Packet

            Arguments:
                ipv4packetbytes -- byte array of ipv4 packet

            Returns:
                Same as socket.sendto
        '''
        assert isinstance(ipv4packetbytes, bytes)
        return self._sock.sendto(ipv4packetbytes, (self._addr, 0))

    def recv(self, bufsize):
        '''
            Receive a TCP/IPv4 Frame.

            Arguments:
                bufsize -- size of buffer

            Returns:
                Same as socket.recv
        '''
        return self._sock.recv(1024)

    def close(self):
        '''Close the socket'''
        self._sock.close()
