import socket
import struct
from pa6.ip import SimpleIPv4Packet


class TCPPacket:
    '''
        This class can be used to build a TCP Payload which can be injected
        into a SimpleIPv4Packet.
    '''

    def __init__(self, src_port, dest_port, ipv4_packet,
                 urg=0, ack=0, psh=0, rst=0, syn=0, fin=0):
        '''
            The Constructor

            Arguments:
                src_port    -- source port to use, must be uint16
                dest_port   -- destination port, must be uint16
                ipv4_packet -- the corresponding SimpleIPv4Packet

            Keyword Arguments:
                urg -- toggle URGENT Flag
                ack -- toggle ACKNOWLEDGMENT Flag
                psh -- toggle PUSH Flag
                rst -- toggle RESET Flag
                syn -- toggle SYNCHRONIZE SEQ Flag
                fin -- toggle FINISH Flag
        '''
        assert isinstance(src_port, int) and 0 < src_port <= 65535
        assert isinstance(dest_port, int) and 0 < dest_port <= 65535
        assert isinstance(ipv4_packet, SimpleIPv4Packet)

        # source- and destination-ports
        self._src_port = src_port
        self._dest_port = dest_port

        # the sequence number
        self._seq_no = 0

        # the acknowledgment number
        self._ack_no = 0

        # this points to the actual data section within the TCP packet
        self._data_offset = 5

        # set tcp flags
        self._tcp_flags = [
            urg % 2,
            ack % 2,
            psh % 2,
            rst % 2,
            syn % 2,
            fin % 2
        ]

        # the window size which can be negotiated
        self._window_size = 43690

        # checksum will be calculated later
        self._checksum = 0

        self._ipv4_packet = ipv4_packet
        self._payload = None

        # construct the payload
        self._construct_payload()

    def _construct_payload(self):
        '''Construct the payload'''

        # padding for data offset
        pad_data_offs = self._data_offset << 4

        # iterate over all flags and create a single byte containing all flags
        i = 0
        flags = 0
        for lshift in reversed(range(0, 6)):
            flags |= self._tcp_flags[i] << lshift
            i += 1

        # construct payload
        tmp_payload = bytearray(struct.pack('!HHLLBBHHH', self._src_port,
                                            self._dest_port, self._seq_no,
                                            self._ack_no, pad_data_offs, flags,
                                            self._window_size, self._checksum,
                                            0))
        # calculate checksum
        self._checksum = self._calc_checksum(tmp_payload)

        # inject correct checksum into tcp header
        tmp_payload[16] = self._checksum >> 8
        tmp_payload[17] = self._checksum & 0x00FF

        self._payload = bytes(tmp_payload)

    def _calc_checksum(self, payload):
        '''
            Calculates the TCP checksum for a given payload

            Arguments:
                payload -- byte-object
            Returns:
                checksum -- 2 bytes, big endian
        '''

        result = 0x0000

        # To calculate the checksum, we need to create a pseudo ipv4-header
        pseudo_header = struct.pack('!4s4sBBH',
                                    self._ipv4_packet._src_addr,
                                    self._ipv4_packet._dest_addr,
                                    0,
                                    self._ipv4_packet.get_protocol(),
                                    len(payload))

        # create a pseudo ipv4-tcp-packet without layer 2
        pseudo_packet = pseudo_header + payload

        # apply zero-padding if needed (number of bytes in packet must be even
        # for checksum calculation)
        if len(payload) % 2 != 0:
            pseudo_packet = pseudo_packet + bytes(0)

        # calculate the sum of the ones-complement of each 2 byte within the
        # packet
        for i in range(0, len(pseudo_packet), 2):
            result += pseudo_packet[i] + (pseudo_packet[i + 1] << 8)

        # finalize and create ones-complement of result
        result = (result >> 16) + (result & 0xFFFF)
        result += (result >> 16)
        return socket.htons(~result & 0xFFFF)

    def bytes(self):
        '''Returns the byte representation'''
        return self._payload
