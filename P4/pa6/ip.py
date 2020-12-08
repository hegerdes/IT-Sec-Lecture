import socket
import struct


class SimpleIPv4Packet:
    """This class represents a simple IPv4 packet"""

    def __init__(self, src_addr, dest_addr, encapsulated_protocol, ttl=255):
        """Constructor

           Arguments:
                src_addr              -- the source address as string
                dest_addr             -- the destination address as string
                encapsulated_protocol -- protocol you want to wrap into ipv4

            Keyword Arguments:
                ttl -- time to live, default=255
        """

        # we are building a pretty simple ipv4 packet frame according to
        # http://www.ietf.org/rfc/rfc791.txt.
        self._version = 4  # the ip version is ipv4

        # the header length is expressed as x times 32 bit length. the most
        # simple ipv4 headers consist of 5 times 32 bit.
        self._ihl = 5

        # the type of service field consists of multiple flags that are used
        # to control and implement various quality of service features.
        # As we probably won't need to use these features, we can set it to 0.
        self._tos = 0

        # the total length of the datagram.
        self._total_len = 20

        # the ID is used for reassembly when sending ip datagrams that are
        # fragmented by max buffer sizes of the tx queue. Since you should only
        # use one datagram when port-scanning using a particular technique,
        # this can be static, we don't need fragmentation and reassembly.
        self._id = 31337

        # this actually represents two fields within the ipv4 header:
        # flags and fragmentation offset, which are both used to control
        # fragmentation. As we don't need this feature, we can set everything
        # to zero.
        self._flags_and_frag_offs = 0

        # "A checksum on the header only. Since some header fields change
        # (e.g., time to live), this is recomputed and verified at each point
        # that the internet header is processed." - RFC 791
        # By the way: this is not crc but rather the sum of all 16bit fields
        # ones-complement.
        # We don't need to calculate the checksum since it's calculated by
        # the kernel.
        self._hdr_checksum = 0

        # the time to live, you don't need to change this parameter. hence,
        # it's optional.
        self._ttl = ttl

        # the next-level protocol wrapped by an ip datagram. Do some research
        # and think about what you need to pass here.
        # Hint: There's a constant described by following link that you can
        # use: https://docs.python.org/3.6/library/socket.html
        self._proto = encapsulated_protocol

        # the source and destination addresses
        self._src_addr = socket.inet_aton(src_addr)
        self._dest_addr = socket.inet_aton(dest_addr)

        # the ip resulting ip packet after constructing the header
        self._packet = None

        # construct the header
        self._construct_hdr()

    def _construct_hdr(self):
        """Construct the Header and save to self._packet"""
        ver_ihl_byte = (self._version << 4) | self._ihl
        tmp_packet = bytearray(
            struct.pack('!BBHHHBBH4s4s', ver_ihl_byte, self._tos,
                        self._total_len, self._id,
                        self._flags_and_frag_offs, self._ttl,
                        self._proto, self._hdr_checksum,
                        self._src_addr, self._dest_addr)
        )
        self._checksum = self._calc_checksum(tmp_packet)

        # inject correct checksum into ipv4 header
        tmp_packet[10] = self._checksum >> 8
        tmp_packet[11] = self._checksum & 0x00FF
        self._packet = bytes(tmp_packet)

    def _calc_checksum(self, payload):
        result = 0x0000
        tmp_payload = bytearray(payload[:20])
        tmp_payload[10] = 0
        tmp_payload[11] = 0
        tmp_payload = bytes(tmp_payload)
        if len(tmp_payload) % 2 != 0:
            tmp_payload = tmp_payload + bytes(0)  # add padding if needed

        for i in range(0, len(tmp_payload), 2):
            result += tmp_payload[i] + (tmp_payload[i + 1] << 8)
        result = (result >> 16) + (result & 0xFFFF)
        result += (result >> 16)
        return socket.htons(~result & 0xFFFF)

    def set_data_payload(self, payload):
        """Use this function to inject your hand-crafted data-payload into
           the IP packet.

           Arguments:
               payload -- the payload to inject, must be bytes-object
        """
        assert isinstance(payload, bytes)
        self._packet = self._packet[:20] + payload
        self._total_len = len(self._packet)
        tmp_packet = bytearray(self._packet)
        tmp_packet[2] = self._total_len >> 8
        tmp_packet[3] = self._total_len & 0x00FF
        self._checksum = self._calc_checksum(tmp_packet)
        tmp_packet[10] = self._checksum >> 8
        tmp_packet[11] = self._checksum & 0x00FF
        self._packet = bytes(tmp_packet)

    def get_src_addr(self):
        """This is used by the RawSocket class"""
        return socket.inet_ntoa(self._src_addr)

    def get_protocol(self):
        return self._proto

    def bytes(self):
        """Returns the built byte object by this instance"""
        return self._packet
