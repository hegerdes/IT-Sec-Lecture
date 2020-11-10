# /usr/bin/env python3

from struct import *

class MQTT_Dissector:

    def parse_tcp_packet(self, src_addr, dst_addr, src_port, dst_port, tcp_payload):
        # pack_format = "!H" + str(len(tcp_payload) - 2) + 's'
        if len(tcp_payload)>0: print(tcp_payload)

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
