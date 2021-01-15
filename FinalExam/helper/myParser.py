import argparse
import sys

class myParser:

    def __init__(self):
        self.versionCheck()
        self.parser = argparse.ArgumentParser(description='Lunches an argparser')
        self.parser.add_argument('--config-file', '-f', help='Config file')

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
                    config = list()
                    [config.append(part.strip()) for part in line.split(':')]
                    if (len(config) != 5): raise ValueError('Illigal length in confogfile: ' + config_path)
                    configs.append(config)
                line = fr.readline()
                break   #TODO Remove!!!
        [print(conf) for conf in configs]
        return configs

