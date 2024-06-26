#!/bin/bash

#Make it pritty
RED='\033[0;31m'
NC='\033[0m'
GRN='\033[0;32m'

#easy config
CA_FILE_NAME="ca"
KEY_SIZE=4096
DST_DIR="certificates"

# Add aditional names for mor clients (seperated by space)
EXAMPLES=(example)

#Set CWD
cd "$(dirname "$0")"

#Check openssl command
if ! command -v openssl &>/dev/null; then
    echo -e "${RED}openssl not be found. Exit${NC}"
    exit
fi

#Create DST-folder
if [ ! -d "$DST_DIR" ]; then
    mkdir -p "$DST_DIR"
fi

#Flags:
# req               request
#-x509              sign
#-batch             no interactive
#-days              num of days it is valid
#-key               what key to use
#-subj              pass parameters that would have been interactive
#-nodes             means no des. Will not encrypt the private key. No passphrase
#-newkey            while request generation generate a new private key instead of using an existing
#-keout             path where to store the new generated key
#-key               path to keyfile to use for request or sign
#-out               path where to store the generated file
#-CA                path of CA tu use for signing
#-CAkey             path of CA pvt  key
#-CAcreateserial    set serialnumber of the signed. Used with-set_serial 01. OPTIONAL
#-config            path of a openssl.conf file with mor options. Moe in the info in openssl.conf. Default is in /etc/ssl/openssl.conf
#-extensions        Used for v3_req with the SAN option

# CA-key
echo -e "${GRN}Creating CA key${NC}"
# Create a private rsa key with the size of KEY_SIZE
openssl genrsa -out $DST_DIR/$CA_FILE_NAME.key $KEY_SIZE
# Err check
if [ $? -ne 0 ]; then
    echo -e "${RED}Error in CA key generation${NC}"
    exit
fi

# Task 2.1
# CA-cert
openssl req -new -key $DST_DIR/$CA_FILE_NAME.key -x509 -days 3650 -batch -subj "/CN=authority-969272/C=DE/ST=LowerSaxony/L=Osnabrueck/O=UNI/OU=StudentSigner/emailAddress=hegerdes@uos.de" -out $DST_DIR/$CA_FILE_NAME.pem

# Err check
if [ $? -ne 0 ]; then
    echo -e"${RED}Error in CA crt generation${NC}"
    exit
fi

for example in ${EXAMPLES[@]}; do
    # Example key and sign-request
    echo -e "${GRN}Creating ${example} key and sign request ${NC}"
    openssl req -new -newkey rsa:$KEY_SIZE -nodes -keyout $DST_DIR/$example.key -batch -subj "/CN=user-969272/C=DE/ST=LowerSaxony/L=Osnabrueck/O=UNI/OU=Student/emailAddress=hegerdes@uos.de" -out $DST_DIR/$example.csr

    if [ $? -ne 0 ]; then
        echo -e "${RED}Error in example key/csr generation${NC}"
        exit
    fi

    # Sign with CA
    echo -e "${GRN}Signing ${example} with CA ${NC}"
    openssl x509 -req -days 365 -in $DST_DIR/$example.csr -CA $DST_DIR/$CA_FILE_NAME.pem -CAkey $DST_DIR/$CA_FILE_NAME.key -CAcreateserial -set_serial 01 -out $DST_DIR/$example.pem

    if [ $? -ne 0 ]; then
        echo -e "${RED}Error at client sign${NC}"
        exit
    fi
done

# Task 2.2 & Task 2.3
CLIENTS=(server client1 client2 client3)
# client3 is not i ACL

for client in ${CLIENTS[@]}; do
    echo -e "${GRN}Creating ${client} key and sign request ${NC}"
    openssl req -new -newkey rsa:$KEY_SIZE -nodes -keyout $DST_DIR/$client.key -batch -out $DST_DIR/$client.csr -config openssl.conf -subj "/CN=${client}-969272/C=DE/ST=LowerSaxony/L=Osnabrueck/O=UNI/OU=${client}/emailAddress=${client}@uos.de"

    if [ $? -ne 0 ]; then
        echo -e "${RED}Error in client key/csr generation${NC}"
        exit
    fi

    # Sign with CA & keep subject alatanative names
    echo -e "${GRN}Signing ${client} with CA ${NC}"
    openssl x509 -req -days 365 -in $DST_DIR/$client.csr -CA $DST_DIR/$CA_FILE_NAME.pem -CAkey $DST_DIR/$CA_FILE_NAME.key -CAcreateserial -set_serial 01 -out $DST_DIR/$client.pem -extfile openssl.conf -extensions v3_req

    if [ $? -ne 0 ]; then
        echo -e "${RED}Error at client sign${NC}"
        exit
    fi
done

# Not signed server
echo -e "${GRN}Not signed server${NC}"
openssl genrsa -out $DST_DIR/NoSignedServer.key $KEY_SIZE
openssl req -new -key $DST_DIR/NoSignedServer.key -x509 -days 3650 -batch -subj "/CN=NoSignServer-969272/C=DE/ST=LowerSaxony/L=Osnabrueck/O=UNI/OU=StudentSigner/emailAddress=hegerdes@uos.de" -out $DST_DIR/NoSignedServer.pem

# Not signed server
echo -e "${GRN}Not signed client${NC}"
openssl genrsa -out $DST_DIR/NoSignedClient.key $KEY_SIZE
openssl req -new -key $DST_DIR/NoSignedClient.key -x509 -days 3650 -batch -subj "/CN=NoSignClient-969272/C=DE/ST=LowerSaxony/L=Osnabrueck/O=UNI/OU=StudentSigner/emailAddress=hegerdes@uos.de" -out $DST_DIR/NoSignedClient.pem

# Bad SubjectAltNames
echo -e "${GRN}Bad SAN${NC}"
openssl req -new -newkey rsa:$KEY_SIZE -nodes -keyout $DST_DIR/badSAN.key -batch -out $DST_DIR/badSAN.csr -config openssl_bad.conf -subj "/CN=${client}-969272/C=DE/ST=LowerSaxony/L=Osnabrueck/O=UNI/OU=${client}/emailAddress=${client}@uos.de"

# Sign with CA & keep subject alatanative names
openssl x509 -req -days 365 -in $DST_DIR/badSAN.csr -CA $DST_DIR/$CA_FILE_NAME.pem -CAkey $DST_DIR/$CA_FILE_NAME.key -CAcreateserial -set_serial 01 -out $DST_DIR/badSAN.pem -extfile openssl_bad.conf -extensions v3_req

echo -e "${GRN}Everything generated succsesfully${NC}"
