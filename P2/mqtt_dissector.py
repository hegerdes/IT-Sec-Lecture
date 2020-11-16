# /usr/bin/env python3

from struct import unpack, error


# Nice formatting
RED='\033[1;31m'
GRN='\033[1;32m'
YEL='\033[1;33m'
BLU='\033[1;34m'
GRY='\033[1;90m'
NC='\033[0m' # No Color



CONNECT = 0b0001
CONNACT = 0b0010
PUBLISH = 0b0011
PUBACT = 0b0100
SUBSCRIBE = 0b1000
SUBACT = 0b1001


class MQTT_Dissector:
    MQTT_FIXED_HEADER_LEN = 2
    MQTT_VAR_HEADER_LEN = 10
    ERR_COUNTER = 0
    #Bitmasks to filter for relevant flags
    BIT_FLAG_MASK = {
        'USER_Flag': 0b10000000,
        'PW_Flag': 0b01000000,
        'RETAIN_Flag': 0b00100000,
        'WILL_QS_Flag': 0b00011000,
        'WILL_Flag': 0b00000100,
        'CLEAN_Flag': 0b00000010,
    }

    def parseFlags(self, flags):
        """ To check the flags. Return a dict with the key=FlagName val=True/False
            For WILL_QS we can have 4 states. So val is either 1,2,3,4
        """

        flags_dict = {}
        for key, val in self.BIT_FLAG_MASK.items():
            if key == 'WILL_QS_Flag':
                #Handling for double bit Will QoS
                # See http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc398718031
                if((flags & val) == 0b00000000): flags_dict[key] = 0
                if((flags & val) == 0b00001000): flags_dict[key] = 1
                if((flags & val) == 0b00010000): flags_dict[key] = 2
                if((flags & val) == 0b0001100): flags_dict[key] = 3 # Invalid state
            else:
                flags_dict[key] = (flags & val) == val

        return flags_dict

    def decodeCharString(self, buffer):
        # Unpackts the first 2 bytes that tells us the length of the String (in bytes)
        length = unpack('!H', buffer[:2])[0]
        # Decodes a string with the length specified by length unpacked before
        return unpack('!' + str(length) + 's', buffer[2:length + 2])[0].decode() , buffer[length + 2:]

    def unspportedErr(self):
        print(RED + '\nParsing not supported yet' + NC)

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

        #Error handling of retrys
        if self.ERR_COUNTER > 10:
            print('Max number of parsing trys reached!\nPlease make sure MQTT packages are sent. Exit')
            exit(0)

        #Set defaults
        USER = None
        PW = None
        try:
            # Only check on packages with len greater 1
            if len(tcp_payload) > 1:
                #print('OriPayload: ' + str(tcp_payload))
                mqtt_fixed_header = tcp_payload[:self.MQTT_FIXED_HEADER_LEN]
                mqtt_no_header = tcp_payload[self.MQTT_FIXED_HEADER_LEN:]
                mqtt_var_header = mqtt_no_header[:self.MQTT_VAR_HEADER_LEN]
                mqtt_payload = mqtt_no_header[self.MQTT_VAR_HEADER_LEN:]

                #Get packet type
                fixed_header = unpack('!H', mqtt_fixed_header)[0]

                #ID and flags
                p_name_len, p_name, p_version, flags, keep_alive = unpack('!H4sbbH', mqtt_var_header)
                client_id, mqtt_payload_rest = self.decodeCharString(mqtt_payload)

                #Convert Flags in dict of features
                flags_dict = self.parseFlags(flags)

                #Connect msg
                if bin(fixed_header >> 12) == bin(CONNECT):
                    print(YEL + 'Captured connecting Packet...' + NC)
                    print(GRY + 'Flags: ' , flags_dict, NC)

                    #If user flag is set
                    if(flags_dict['USER_Flag']):
                        USER, mqtt_payload_rest = self.decodeCharString(mqtt_payload_rest)
                        print(GRN + 'User: ' + NC + USER)

                    #If pw flag is set
                    if(flags_dict['PW_Flag']):
                        PW, mqtt_payload_rest = self.decodeCharString(mqtt_payload_rest)
                        print(GRN + 'PW: ' + NC + PW)

                    if(len(mqtt_payload_rest) == 0):
                        print(GRY + 'Everyting parsed' + NC)
                        #Done
                        return USER, PW

                # For future use. For now it is out of the assaigment scope
                if bin(fixed_header >> 12) == bin(CONNACT):         #CONNACK package
                    print(YEL + 'Captured conn-act Packet...' + NC)
                    self.unspportedErr()
                if bin(fixed_header >> 12) == bin(SUBSCRIBE):       #SUBSCRIBE package
                    print(YEL + 'Captured subscribe Packet...' + NC)
                    self.unspportedErr()
                if bin(fixed_header >> 12) == bin(PUBLISH):         #PUBLISH package
                    print(YEL + 'Captured publish Packet...' + NC)
                    self.unspportedErr()
                # NOTE: There are still some othere packet types.
                # These are not relevant for this task.
                # Please refer to http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc398718026

        except error:   #struct error
            print('Err, parsing packet. Trying next one...')
            self.ERR_COUNTER += 1
        except UnicodeDecodeError:
            self.ERR_COUNTER += 1
            self.unspportedErr()
        except KeyboardInterrupt:
            print('Keyboard interrupt recceived. Exiting...')
            exit(0)
        except:
            print('Something went wrong')
            self.ERR_COUNTER += 1


        # return if username and password not found => Default is NONE, NONE
        return USER, PW