# /usr/bin/env python3


class MQTT_Dissector:

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
        
        # TODO: Implement me

        # return if username and password not found
        return None, None
