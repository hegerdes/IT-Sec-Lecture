#!/usr/bin/python3

import argparse
import sys


class color:
    # Nice formatting
    RED = '\033[1;31m'
    GRN = '\033[1;32m'
    YEL = '\033[1;33m'
    BLU = '\033[1;34m'
    GRY = '\033[1;90m'
    NC = '\033[0m'  # No Color


class constants:
    REV_BUFFER = 4096

    PROT_ID = b'YPROX'
    FIXED_HEADER = 6
    BIT_FLAG_MASK = {
        'CON_Flag':             0b00000000,
        'CON_ACK_Flag':         0b00000001,
        'DST_FAIL_Flag':        0b01000000,
        'LOC_FAIL_Flag':        0b11000000,
        'END_Flag':             0b00100000,
        'RPL_RADY_Flag':        0b10100000,
        'PROT_ERR_Flag':        0b01100000,
    }


class Config:

    def __init__(self, dst_host='icanhazip.com', dst_port=80, remote_host='bones.informatik.uni-osnabrueck.de', remote_port=8001, listen_port=8000, ssl_options=None):
        super().__init__()
        self.dst = {'host': dst_host, 'port': int(dst_port)}
        self.remote = {'host': remote_host, 'port': int(remote_port)}
        self.local = {'host': '127.0.0.1', 'port': int(listen_port)}
        self.ssl = ssl_options

    def __str__(self):
        return 'Conf: dst={}, remote={}, local={}, ssl={}'.format(tuple(self.dst.values()), tuple(self.remote.values()), tuple(self.local.values()), self.ssl)

    def setSSL(self, ssl_options):
        self.ssl = ssl_options


class ProxyParser:

    def __init__(self):
        self.versionCheck()
        self.parser = argparse.ArgumentParser(
            description='Lunches an argparser')
        self.parser.add_argument(
            '--certificate', '-c', help='Certificate path', default=None)
        self.parser.add_argument(
            '--key', '-k', help='Pvt key path', default=None)
        self.parser.add_argument(
            '--ca', '-C', help='CA certificate path', default=None)
        self.args = None
        self.configs = None

    def versionCheck(self):
        if sys.version_info < (3, 8, 0):
            sys.stderr.write("You need python 3.8 or later to run this\n")
            sys.exit(1)

    def parseArgs(self):
        self.args = self.parser.parse_args()
        return self.args

    def setSSLConf(self):
        ssl_keys, ssl_options = ['certificate', 'key', 'ca'], {}

        # Err check
        if not self.configs:
            self.parseConfig()

        for k, v in dict(self.args._get_kwargs()).items():
            if k in ssl_keys and v:
                ssl_options[k] = v

        [conf.setSSL(ssl_options) for conf in self.configs]
        return self.configs

    def parseConfig(self, config_path=None):
        self.configs = list()

        # Default
        if not config_path:
            # Err prevention
            if not self.args:
                self.parseArgs()
            config_path = self.args.config_file

        with open(config_path, "r") as fr:
            line = fr.readline()
            while line:
                if line[0] != '#' and len(line) != 1:
                    conf = list()
                    [conf.append(part.strip()) for part in line.split(':')]
                    if (len(conf) != 5):
                        raise ValueError(
                            'Illigal length in confogfile: ' + config_path)
                    self.configs.append(Config(*conf))
                line = fr.readline()
        return self.configs
