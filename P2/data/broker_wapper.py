# uncompyle6 version 3.7.4
# Python bytecode 3.8 (3413)
# Decompiled from: Python 3.8.6 (default, Sep 25 2020, 09:36:53) 
# [GCC 10.2.0]
# Embedded file name: /media/sf_VBox/broker_wrapper.py
# Compiled at: 2020-09-17 17:02:17
# Size of source mod 2**32: 3765 bytes
"""
broker_wrapper.py, a utility class to start one or more mosquitto broker(s).
Monitors the processes and can terminate them.

THIS FILE MUST NOT BE EDITED! ALL CHANGES WILL BE IGNORED

@author: tzimmermann @ AG Verteilte Systeme, Uni Osnabrueck
@date: 28.03.2018
@author: atessmer @ AG Verteilte Systeme, Uni Osnabrueck
@date: 03.09.2020
"""
import subprocess as s, tempfile, time, shutil
from sys import platform
import os

class Mosquitto:
    __doc__ = "\n    Create a broker Object.\n    @param port: Port where the broker will start (Default: 1883)\n    @param credentials: a list of (username, password) tuples which are allowed\n                        or None, then no authentication will be used!\n    @raise NotImplementedError  if the OS is not posix compatible (Linux, Unix...)\n                                As the clientsConnected counting won't work there\n    "

    def __init__(self, port=1883, credentials=None, verbose=True):
        self.verbose = verbose
        self.tmp = tempfile.mkdtemp(prefix='PA2_')
        self.conf = self.tmp + '/mosquitto.conf'
        self.passwd = self.tmp + '/mqpass'
        self.credentials = credentials
        self.port = port
        self.serverProcess = None
        if not platform == 'linux':
            if platform == 'linux2':
                pass
            else:
                raise NotImplementedError('This Class currently only runs on *nix systems')

    def start(self):
        with open(self.conf, 'w') as (file):
            if isinstance(self.credentials, list):
                s.call(['touch', self.passwd])
                s.call(['touch', self.conf])
                for user, pw in self.credentials:
                    s.call(['/usr/bin/mosquitto_passwd', '-b', self.passwd, user, pw])
                else:
                    file.write('allow_anonymous  false\n')
                    file.write('password_file  {}\n'.format(self.passwd))

                if self.verbose == False:
                    file.write('log_dest none\n')
            else:
                print('Warning! No credentials given, allowing anonymus login!')
            file.write('listener ' + str(self.port) + '\n')
        self.serverProcess = s.Popen(['/usr/sbin/mosquitto', '-c', self.conf])

    def stop(self):
        self.serverProcess.terminate()
        time.sleep(1)
        self.serverProcess.kill()

    def isRunning(self):
        return self.serverProcess is not None and self.serverProcess.poll() is None

    def clientsConnected(self):
        if self.isRunning():
            stdout, stderr = s.Popen(('ls -l /proc/' + str(self.serverProcess.pid) + '/fd | grep socket | wc -l'), shell=True, stdout=(s.PIPE)).communicate()
            return int(int(stdout.strip())) - 1
        return 0

    def __del__(self):
        if self.serverProcess is not None:
            self.serverProcess.terminate()
            time.sleep(1)
            self.serverProcess.kill()
            self.serverProcess.wait()
        shutil.rmtree((self.tmp), ignore_errors=True)
# okay decompiling broker_wrapper.pyc
