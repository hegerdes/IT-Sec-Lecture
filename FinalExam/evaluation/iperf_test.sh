#!/bin/bash

# Kill all prosesses in the same group as script
trap "kill 0" EXIT

#HOWTO:
#Start the proxy server first. Use the -t flag for test mode or --test
#You may need to edit the config or the server host depending on the machine you run it on

#Make it pritty
RED='\033[0;31m'
NC='\033[0m'
GRN='\033[0;32m'

ITERATIONS=15
PACKAGE_SIZE=16MB
SERVER="diggory"
LOG_FILE="iperf_${SERVER}_new_8.log"

#Set CWD
cd "$(dirname "$0")"

echo -e "${GRN}Starting clients in background${NC}"
python3 ../proxy_client.py -f ../conf/config_iperf_bones.txt -t &
python3 ../ssh_proxy_client.py -f ../conf/config_ssh.txt &

echo -e "${GRN}Running tests with ${ITERATIONS} interations and ${PACKAGE_SIZE} package-size ${NC}"
for iteration in $(seq 1 $ITERATIONS); do
    echo "NoProxy" >> $LOG_FILE
    iperf -c ${SERVER}.informatik.uni-osnabrueck.de -i 0.5 -p 2622 -n $PACKAGE_SIZE -N >> $LOG_FILE

    echo "ProxyNoSSL" >> $LOG_FILE
    iperf -c 127.0.0.1 -i 0.5 -p 8000 -n $PACKAGE_SIZE -N >> $LOG_FILE

    echo "ProxyServerSSL" >> $LOG_FILE
    iperf -c 127.0.0.1 -i 0.5 -p 8001 -n $PACKAGE_SIZE -N >> $LOG_FILE

    echo "ProxyServerClientSSL" >> $LOG_FILE
    iperf -c 127.0.0.1 -i 0.5 -p 8002 -n $PACKAGE_SIZE -N >> $LOG_FILE

    echo "ProxyServerClientSSLACL" >> $LOG_FILE
    iperf -c 127.0.0.1 -i 0.5 -p 8003 -n $PACKAGE_SIZE -N >> $LOG_FILE

    echo "SSHTunnel" >> $LOG_FILE
    iperf -c 127.0.0.1 -i 0.5 -p 2222 -n $PACKAGE_SIZE -N >> $LOG_FILE
done

echo -e "${GRN}Test done! Killing background tasks ${NC}"