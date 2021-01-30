#!/bin/bash

#Make it pritty
RED='\033[0;31m'
NC='\033[0m'
GRN='\033[0;32m'

ITERATIONS=1
LOG_FILE='iperf.log'

#Set CWD
cd "$(dirname "$0")"
PACKAGE_SIZE=12MB

for iteration in $(seq 1 $ITERATIONS); do
    echo "NoProxy" >> $LOG_FILE
    iperf -c bones.informatik.uni-osnabrueck.de -i 0.5 -l 8KB -p 2622 -n $PACKAGE_SIZE >> $LOG_FILE

    echo "ProxyNoSSL" >> $LOG_FILE
    iperf -c 127.0.0.1 -i 0.5 -l 8KB -p 8000 -n $PACKAGE_SIZE >> $LOG_FILE

    echo "ProxyServerSSL" >> $LOG_FILE
    iperf -c 127.0.0.1 -i 0.5 -l 8KB -p 8001 -n $PACKAGE_SIZE >> $LOG_FILE

    echo "ProxyServerClientSSL" >> $LOG_FILE
    iperf -c 127.0.0.1 -i 0.5 -l 8KB -p 8002 -n $PACKAGE_SIZE >> $LOG_FILE

    echo "ProxyServerClientSSLACL" >> $LOG_FILE
    iperf -c 127.0.0.1 -i 0.5 -l 8KB -p 8003 -n $PACKAGE_SIZE >> $LOG_FILE
done