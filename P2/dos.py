#!/usr/bin/env python3

"""
dos.py, Crashes a vulnerable mosqsuitto broker
@author: tzimmermann @ AG Verteilte Systeme, Uni Osnabrueck
@date: 19.03.2018
"""


class MQTT_DoS:

    def __init__(self, hostname, port, credentials):
        """Constructor sets up a Denial of Service Attack
           :param string hostname: Hostname or IP of the broker
           :param int port: Port of the broker
           :param tuple credentials: tuple of valid username and password for a client
           """
           
        # TODO: Implement me


    def run(self):
        """Start new paho-mqtt clients until the broker seems crashed, then return
           :return : return without value if broker has crashed
           """
        
        # Block till broker seems crashed
        # TODO: Implement me
        
        # return if broker has crashed
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launches multiple mqtt-subscribers until the broker crashes')
    parser.add_argument('--broker', '-b',
                        help='hostname or ip of the broker to connect to',
                        default='localhost')
    parser.add_argument('--port', '-p',
                        help='port of the broker',
                        default='1883',
                        type=int)
    parser.add_argument('--user', '-u',
                        help='user',
                        default='username',
                        type=str)
    parser.add_argument('--password', '-P',
                        help='password',
                        default='Password for >username<',
                        type=str)
    args = parser.parse_args()
    crasher = MQTT_DoS(args.broker, args.port, (args.user, args.password))
    crasher.run()
