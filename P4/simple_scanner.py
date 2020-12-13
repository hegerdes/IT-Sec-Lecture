#!/usr/bin/python3
import socket
import sys
import re

# Nice formatting
RED = '\033[1;31m'
GRN = '\033[1;32m'
YEL = '\033[1;33m'
BLU = '\033[1;34m'
GRY = '\033[1;90m'
NC = '\033[0m'  # No Color


# Help MSG and usage
def printUsage():
    print('Start with ./simple_scanner.py TARGET START_PORT END_PORT')


# Port check
def checkPort(ip, port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        conn.connect((ip, port))
        conn.close
        return True
    except socket.error:
        return False


if __name__ == "__main__":
    if len(sys.argv) != 4:
        printUsage()
        exit(0)

    pattern = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    try:
        host = sys.argv[1]
        start_port = int(sys.argv[2])
        end_port = int(sys.argv[3])

        # host = '127.0.0.1'
        # start_port = 22300
        # end_port = start_port + 500
        # Sanity check
        if not pattern.match(host):
            raise ValueError('Not a valid IP')
        if start_port >= 65535 or end_port >= 65535:
            raise ValueError('Port to big')
        if start_port < 0 or end_port < 0:
            raise ValueError('Port to small')
        if start_port > end_port:
            raise ValueError('Start port must be smaller than end port')

    except ValueError:
        print('Please provide a valid number')
        printUsage()
        exit(0)

    #Run check
    try:
        for i in range(start_port, end_port + 1):
            if checkPort(host, i):
                print(GRN + 'Port', i, 'is open')

        print(GRY + 'Scan done!' + NC)
    except KeyboardInterrupt:
        print("Interrupt received, stopping server..")
        exit(0)
