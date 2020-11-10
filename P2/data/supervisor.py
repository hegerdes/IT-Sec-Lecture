# uncompyle6 version 3.7.4
# Python bytecode 3.8 (3413)
# Decompiled from: Python 3.8.6 (default, Sep 25 2020, 09:36:53) 
# [GCC 10.2.0]
# Embedded file name: supervisor.py
# Compiled at: 2020-09-03 13:23:24
# Size of source mod 2**32: 7252 bytes
"""
supervisor.py, launches and supervises a mosquitto broker,
publishes sensor values and displays them

THIS FILE MUST NOT BE EDITED! ALL CHANGES WILL BE IGNORED

@author: tzimmermann @ AG Verteilte Systeme, Uni Osnabrueck
@date: 19.03.2018
@author: atessmer @ AG Verteilte Systeme, Uni Osnabrueck
@date: 03.09.2020
"""
import argparse
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import random, socket, string, sys, time, subprocess, broker_wrapper

class bcolors:
    HEADER = '\x1b[95m'
    OKBLUE = '\x1b[94m'
    OKGREEN = '\x1b[92m'
    WARNING = '\x1b[93m'
    FAIL = '\x1b[91m'
    ENDC = '\x1b[0m'
    BOLD = '\x1b[1m'
    UNDERLINE = '\x1b[4m'


class Supervisor:

    def __init__(self, start_port=1883, random_client_id=False, random_cred=False, random_crash_count=False, verbose=False):
        self.topic = '/smart/supervisor/emergency/thermostat/current_temperature'
        self.broker = None
        self.subscriber = None
        self.port = start_port
        self.verbose = verbose
        self.lispass = 'insecure_subscriber_password'
        self.lisuser = 'legit_subscriber'
        if random_cred:
            self.senuser = 'pub_{}'.format(self._Supervisor__gen_random_string(10, 20))
            self.senpass = self._Supervisor__gen_random_string()
        else:
            self.senuser = 'legit_publisher'
            self.senpass = 'insecure_publisher_password'
        if random_crash_count:
            self.clients_to_crash = random.randint(10, 42)
        else:
            self.clients_to_crash = 42
        if random_client_id:
            self.pub_client_id = 'sup_pub_' + self._Supervisor__gen_random_string(3, 10)
        else:
            self.pub_client_id = 'sup_pub_007'
        print('Current settings')
        print('Publisher username: {}, password: {}, client_id: {}'.format(self.senuser, self.senpass, self.pub_client_id))
        print('Clients to crash: {}'.format(self.clients_to_crash))

    def __gen_random_string(self, min_length=10, max_length=30):
        return ''.join([random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(random.randint(min_length, max_length))])

    def port_free(self, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('127.0.0.1', port))
        except socket.error:
            return False
        else:
            try:
                s.shutdown(socket.SHUT_RDWR)
                s.close()
            except socket.error:
                pass
            else:
                return True

    def start_subscriber(self, port):
        self.subscriber = mqtt.Client(self.lisuser)
        self.subscriber.username_pw_set(self.lisuser, self.lispass)
        self.subscriber.connect_async('127.0.0.1', port)
        self.subscriber.on_connect = self.on_subscriber_connect
        self.subscriber.on_message = self.cb_on_message
        self.subscriber.loop_start()

    def on_subscriber_connect(self, client, userdata, flags, rc):
        self.subscriber.subscribe(self.topic)

    def cb_on_message(self, client, userdata, msg):
        temp = float(msg.payload)
        if temp >= 68:
            print('{}Temperature: {:.2f}°C -- WARNING, Fire detected!{} -- #Connected clients: {}'.format(bcolors.FAIL, temp, bcolors.ENDC, self.broker.clientsConnected()))
        else:
            print('{}Temperature: {:.2f}°C -- OK{} -- #Connected clients: {}'.format(bcolors.OKGREEN, temp, bcolors.ENDC, self.broker.clientsConnected()))

    def stop_subscriber(self):
        if self.subscriber is not None:
            self.subscriber.disconnect()

    def __kill_all_mosquitto(self):
        subprocess.run(['pkill', '-9', 'mosquitto'])

    def start(self):
        self._Supervisor__kill_all_mosquitto()
        while True:
            if self.broker is None:
                while not self.port_free(self.port):
                    print(str(self.port) + ' is already taken, trying next port')
                    self.port += 1

                print('Starting Broker on Port ' + str(self.port))
                self.broker = broker_wrapper.Mosquitto(self.port, [(self.lisuser, self.lispass),
                 (
                  self.senuser, self.senpass)], self.verbose)
                self.broker.start()
                self.start_subscriber(self.port)
            else:
                if self.broker.isRunning():
                    try:
                        message = random.uniform(50, 90)
                        if message < 68:
                            message = random.uniform(20, 26)
                        publish.single((self.topic), message,
                          client_id=(self.pub_client_id),
                          hostname='127.0.0.1',
                          auth={'username':self.senuser, 
                         'password':self.senpass})
                    except Exception as e:
                        try:
                            print(str(e))
                            print("Legit publisher can't publish it's temperature. Alerting the administrator!")
                            sys.exit(1)
                        finally:
                            e = None
                            del e

                    else:
                        if self.broker.clientsConnected() >= self.clients_to_crash:
                            self.broker.stop()
                            del self.broker
                            self.broker = None
                            time.sleep(10)
                            self.stop_subscriber()
                else:
                    del self.broker
                    self.broker = None
            time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts a mosquitto broker, the temperature-publisher and displays them.')
    parser.add_argument('--random-client-id', '-i', help='Use a random publisher client id',
      action='store_true')
    parser.add_argument('--random-credentials', '-r', help='Use random publisher credentials (username and password)',
      action='store_true')
    parser.add_argument('--random-crash-count', '-c', help='Require a random number of clients to crash the broker',
      action='store_true')
    parser.add_argument('--port', '-p', help='initial port of the broker',
      default='1883',
      type=int)
    parser.add_argument('--verbose', '-v', help='Enable Mosquitto output', action='store_true')
    args = parser.parse_args()
    supervisor = Supervisor(args.port, args.random_client_id, args.random_credentials, args.random_crash_count, args.verbose)
    supervisor.start()
# okay decompiling supervisor.pyc
