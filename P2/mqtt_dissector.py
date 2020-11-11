# /usr/bin/env python3

from struct import *

CONNECT = 0b0001
CONNACT = 0b0010
PUBLISH = 0b0011
PUBACT = 0b0100
SUBSCRIBE = 0b1000
SUBACT = 0b1001


class MQTT_Dissector:
    MQTT_FIXED_HEADER_LEN = 2
    MQTT_VAR_HEADER_LEN = 10
    BIT_FLAG_MASK = {
        'USER_Flag': 0b10000000,
        'PW_Flag': 0b01000000,
        'RETAIN_Flag': 0b00100000,
        'WILL_QS_Flag': 0b00011000,
        'WILL_Flag': 0b00000100,
        'CLEAN_Flag': 0b00000010,
    }

    def parseFlags(self, flags):
        # To check the flags. Return a dict with the key=FlagName val=True/False

        flags_dict = {}
        for key, val in self.BIT_FLAG_MASK.items():
            flags_dict[key] = (flags & val) == val

        return flags_dict

    def decodeChars(self, buffer):
        length = unpack('!H', buffer[:2])[0]
        return unpack('!' + str(length) + 's', buffer[2:length + 2])[0].decode() , buffer[length + 2:]


    def parse_tcp_packet(self, src_addr, dst_addr, src_port, dst_port, tcp_payload):
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
        USER = None
        PW = None
        # Only check on packages with len greater 1
        if len(tcp_payload) > 1:
            #print('OriPayload: ' + str(tcp_payload))
            mqtt_fixed_header = tcp_payload[:self.MQTT_FIXED_HEADER_LEN]
            mqtt_no_header = tcp_payload[self.MQTT_FIXED_HEADER_LEN:]
            mqtt_var_header = mqtt_no_header[:self.MQTT_VAR_HEADER_LEN]
            mqtt_payload = mqtt_no_header[self.MQTT_VAR_HEADER_LEN:]

            fixed_header = unpack('!H', mqtt_fixed_header)[0]
            p_name_len, p_name, p_version, flags, keep_alive = unpack('!H4sbbH', mqtt_var_header)
            client_id, mqtt_payload_rest = self.decodeChars(mqtt_payload)

            #Convert Flags in dict of features
            flags_dict = self.parseFlags(flags)

            #Connect msg
            if bin(fixed_header >> 12) == bin(CONNECT):
                print('Captured connecting Packet...')
                if(flags_dict['USER_Flag']):
                    USER, mqtt_payload_rest = self.decodeChars(mqtt_payload_rest)
                    print(USER)
                if(flags_dict['PW_Flag']):
                    PW, mqtt_payload_rest = self.decodeChars(mqtt_payload_rest)
                    print(PW)
                if(len(mqtt_payload_rest) == 0): print('Everyting parsed')

            if bin(fixed_header >> 12) == bin(CONNACT):
                print('ConnACT...')
            if bin(fixed_header >> 12) == bin(SUBSCRIBE):
                print('Subscribe...')
            if bin(fixed_header >> 12) == bin(PUBLISH):
                print('Publish...')

        # return if username and password not found
        return USER, PW
