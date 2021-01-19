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
    REV_BUFFER = 1024

    PROT_ID = b'YPROX'
    FIXED_HEADER = 6
    BIT_FLAG_MASK = {
    'CON_Flag':             0b00000000,
    'CON_ACK_Flag':         0b10000000,
    'DST_FAIL_Flag':        0b01000000,
    'LOC_FAIL_Flag':        0b11000000,
    'END_Flag':             0b00100000,
    'RPL_RADY_Flag':        0b10100000,
    'PROT_ERR_Flag':        0b01100000,
    }


class Config:

    def __init__(self, dst_host='icanhazip.com', dst_port=80, remote_host='bones.informatik.uni-osnabrueck.de', remote_port=22, listen_port=8000):
        super().__init__()
        self.dst = (dst_host, int(dst_port))
        self.remote = (remote_host, int(remote_port))
        self.local = ('127.0.0.1', int(listen_port))

    def __str__(self):
        return 'Conf: dst={}, remote={}, local={}'.format(self.dst, self.remote, self.local)


class ProxyParser:

    def __init__(self):
        self.versionCheck()
        self.parser = argparse.ArgumentParser(
            description='Lunches an argparser')

    def versionCheck(self):
        if sys.version_info < (3, 8, 0):
            sys.stderr.write("You need python 3.8 or later to run this\n")
            sys.exit(1)

    def parseArgs(self):
        return self.parser.parse_args()

    def parseConfig(self, config_path):
        configs = list()
        with open(config_path, "r") as fr:
            line = fr.readline()
            while line:
                if line[0] != '#' and len(line) != 1:
                    conf = list()
                    [conf.append(part.strip()) for part in line.split(':')]
                    if (len(conf) != 5):
                        raise ValueError(
                            'Illigal length in confogfile: ' + config_path)
                    configs.append(Config(*conf))
                line = fr.readline()
        [print(conf) for conf in configs]
        return configs
