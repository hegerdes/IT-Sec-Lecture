# /usr/bin/env python3

from struct import *

CONNECT = 0b0001
CONNACT = 0b0010
PUBLISH = 0b0011
PUBACT = 0b0100
SUBSCRIBE = 0b1000
SUBACT = 0b1001

def reverse_Bits(n):
        result = 0
        for i in range(16):
            result <<= 1
            result |= n & 1
            n >>= 1
        return result

class MQTT_Dissector:
    MQTT_FIXED_HEADER_LEN = 2

    def parse_tcp_packet(self, src_addr, dst_addr, src_port, dst_port, tcp_payload):
        if len(tcp_payload)>1:
            print('OriPayload: ' + str(tcp_payload))
            mqtt_header = tcp_payload[:self.MQTT_FIXED_HEADER_LEN]
            print('OriHeader: ' + str(mqtt_header))
            header = unpack('!H', mqtt_header)[0]
            print(header)

            # Header first byte = 1
            if bin(header>>12) == bin(CONNECT):
                print('Connecting...')
            if bin(header>>12) == bin(CONNACT):
                print('ConnACT...')
            if bin(header>>12) == bin(SUBSCRIBE):
                print('Subscribe...')
            if bin(header>>12) == bin(PUBLISH):
                print('Publish...')
            # exit(1)

        # mid, packet = unpack(pack_format, tcp_payload)
        # print(mid)
        # print(packet)
        """Dissect TCP payload to identify and extract the username and password from
           a MQTT Connect message.

           :param string src_addr: IPv4 source address (dotted decimal)
           :param string dst_addr: IPv4 destination address (dotted decimal)
           :param int src_port: TCP source port
           :param int dst_port: TCP destination port
           :param bytes tcp_payload: TCP payload
           :return string username: Extracted username (default: None)
           :return string password: Extracted password (default: None)
           """

        # TODO: Implement me

        # return if username and password not found
        return None, None
