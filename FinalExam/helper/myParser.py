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

class Config:

    def __init__(self, dst_host, dst_port, remote_host, remote_port, listen_port):
            super().__init__()
            self.dst = (dst_host, int(dst_port))
            self.remote = (remote_host, int(remote_port))
            self.local = ('127.0.0.1', int(listen_port))

    def __str__(self):
            return 'Conf: dst={}, remote={}, local={}'.format(self.dst, self.remote, self.local)



class myParser:


    def __init__(self):
        self.versionCheck()
        self.parser = argparse.ArgumentParser(description='Lunches an argparser')
        self.parser.add_argument('--config-file', '-f', help='Config file', default='conf/config.txt')

    def versionCheck(self):
        if sys.version_info<(3,8,0):
            sys.stderr.write("You need python 3.8 or later to run this\n")
            sys.exit(1)

    def parseArgs(self):
        return self.parser.parse_args()

    def parseConfig(self, config_path):
        configs = list()
        with open(config_path, "r") as fr:
            line = fr.readline()
            while line:
                if line[0] != '#' and len(line) !=1:
                    conf = list()
                    [conf.append(part.strip()) for part in line.split(':')]
                    if (len(conf) != 5): raise ValueError('Illigal length in confogfile: ' + config_path)
                    configs.append(Config(*conf))
                line = fr.readline()
                break   #TODO Remove!!!
        [print(conf) for conf in configs]
        return configs

