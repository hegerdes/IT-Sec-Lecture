#!/usr/bin/python3

import argparse
import sys

if __name__ == "__main__":

    if sys.version_info<(3,8,0):
        sys.stderr.write("You need python 3.5 or later to run this script\n")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Launches many moqtt-subscribers to crash the broker and launches a new one')