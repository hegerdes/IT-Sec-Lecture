#!/bin/bash

RED='\033[0;31m'
NC='\033[0m'
GRN='\033[0;32m'

CA_FILE_NAME="ca"
# Add aditional names for mor clients (seperated by space)
CLIENTS=(example)

if ! command -v openssl &> /dev/null
then
    echo -e "${RED}openssl not be found. Exit${NC}"
    exit
fi

# CA-key
openssl genrsa -out $CA_FILE_NAME.key 2048
# Err check
if [ $? -ne 0 ]; then
    echo -e "${RED}Error in CA key generation${NC}"
    exit
fi

# CA-cert
openssl req -new -key $CA_FILE_NAME.key -x509 -days 3650 -batch -subj "/CN=authority-969272/C=DE/ST=LowerSaxony/L=Osnabrueck/O=UNI/OU=StudentSigner/emailAddress=hegerdes@uos.de" -out $CA_FILE_NAME.pem
# Err check
if [ $? -ne 0 ]; then
    echo -e"${RED}Error in CA crt generation${NC}"
    exit
fi

for client in ${CLIENTS[@]}; do
    # Example key and sign-request
    openssl req -new -newkey rsa:2048 -nodes -keyout $client.key -days 3650 -batch -subj "/CN=user-969272/C=DE/ST=LowerSaxony/L=Osnabrueck/O=UNI/OU=Student/emailAddress=hegerdes@uos.de" -out $client.csr

    if [ $? -ne 0 ]; then
        echo -e "${RED}Error in client key/csr generation${NC}"
        exit
    fi

    # Sign with CA
    openssl x509 -req -days 365 -in $client.csr -CA $CA_FILE_NAME.pem -CAkey $CA_FILE_NAME.key -CAcreateserial -set_serial 01 -out $client.pem

    if [ $? -ne 0 ]; then
        echo -e "${RED}Error at client sign${NC}"
        exit
    fi
done

echo -e "${GRN}Everything generated succsesfully${NC}"

