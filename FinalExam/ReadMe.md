# Final Task ITS

**Disclaimer:**
Some of the libs on bones/diggory are pretty old. Please considure this while running our code.

I added a *requirements.txt* file form kali with exact version numbers that matches the kali VM setup.

## Task 1
### Task 1.1
All reusable code can be found in *ProxyParser* and *BaseProxy*.

### Task 1.2
```bash
# SSH Tunnel with ssh comand
ssh -L 127.0.0.1:8000:icanhazip.com:80 my_user@bones.informatik.uni-osnabrueck.de -p 22 -N
```
This command gets wrapped in a python subprocess call.

**Alternative:** Usage of ssh lib paramiko. This creates *one* ssh connection and shares it with all ProxyClients. Gives more control and is more elegant

### Task 1.3 & 1.4
Both server and client are using the *Tunnel* class form the *BaseProxy*. It creates a TCP socket-server that listens on the host:port provided by the config. *Tunnel* requires a custom handler that gets called every time a request arrives at the server or client. These handlers are implemented in *proxy_client.py* and *proxy_server.py*.

These handlers first exchange some flags to ensure combability and sets up the rely logic on successes. Else the connection is closed.


---
## Task 2
### Task 2.1
```bash
# CA-key
openssl genrsa -out ca.key 2048

# CA-cert
openssl req -new -key ca.key -x509 -days 3650 -batch -subj "/CN=authority-969272" -out ca.pem

# Example key and sign-request
openssl req -new -newkey rsa:2048 -nodes -keyout example.key -days 3650 -batch -subj "/CN=student-969272" -out example.csr

# Sign with CA
openssl x509 -req -days 365 -in example.csr -CA ca.pem -CAkey ca.key -CAcreateserial -set_serial 01 -out example.pem
```
More options and generation for other keys are in the *initilize.sh* script

### Task 2.2 - Certs
**NOTE:** This is all done in the *initilise.sh* script
```bash
# Server and client certs

# use conf file
openssl req -new -newkey rsa:2048 -nodes -keyout test.key -batch -out test.csr -config openssl.conf -subj "/CN=server-969272/C=DE/ST=LowerSaxony/L=Osnabrueck/O=UNI/OU=Student/emailAddress=hegerdes@uos.de"

#sign
openssl x509 -req -days 365 -in test.csr -CA ca.pem -CAkey ca.key -CAcreateserial -set_serial 01 -out test.pem -extfile openssl.conf -extensions v3_req
```
**Conf file for openssl (Server, Client)**
```Conf
[ req ]
default_bits       = 2048
distinguished_name = req_distinguished_name
req_extensions     = v3_req
promt              = no

[ req_distinguished_name ]
countryName                = DE
stateOrProvinceName        = LowerSaxony
localityName               = Osnabrueck
organizationName           = UNI
commonName                 = server-969272
commonName_max             = 64
commonName_default         = server-969272
emailAddress                    = server@uos.de
emailAddress_max                = 64
emailAddress_default            = info@uos.de

[ v3_req ]
keyUsage = keyEncipherment, dataEncipherment, digitalSignature
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1   =           bones.informatik.uni-osnabrueck.de
DNS.2   =           diggory.informatik.uni-osnabrueck.de
DNS.3   =           www.bones.informatik.uni-osnabrueck.de
DNS.4   =           www.diggory.informatik.uni-osnabrueck.de
DNS.5   =           localhost
IP.1    =           131.173.33.209
IP.2    =           131.173.33.211
IP.3    =           127.0.0.1
```
### Task 2.2 & 2.2 - Implement
**First:** Create certs that a signed with your CA, contain `extendedKeyUsage = serverAuth, clientAuth` and `subjectAltName=[LIST_OF_DNS_NAMES]`

#### ServerSide
For the server init ssl and wrap the socket with:
```Python
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(conf.ssl['certificate'], conf.ssl['key'])

# Wrap the socket
self.socket = ctx.wrap_socket(self.socket, server_side=True)
```
After that you bind the socket.

The client also inits with:
```Python
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
ctx.verify_mode = ssl.CERT_REQUIRED
ctx.check_hostname = True
ctx.load_verify_locations(conf.ssl['ca'])
ctx.load_cert_chain(conf.ssl['certificate'], conf.ssl['key'])

#And than wraps with:
proxy_server_sock = ctx.wrap_socket(proxy_server_sock, server_hostname=conf.remote['host'])
```

#### ClientSide
Is the some as ServerSide but you need to add `Purpose.SERVER_AUTH` and `ctx.verify_mode = ssl.CERT_REQUIRED` as well as the CA-path:
```Python
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

# Client auth enabled
if 'ca' in conf.ssl and conf.ssl['ca']:
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations('pki/certificates/ca.pem')
ctx.load_cert_chain(conf.ssl['certificate'], conf.ssl['key'])

# Wrap the socket
self.socket = ctx.wrap_socket(self.socket, server_side=True)
```
### Task 2.4
All configurations where testet on a local socket on on the bones server.

---
## Task 3

I used iperf server on one testserver (diggory) and the proxy server on another (bones). The local iperf client connected to a local proxy-client and performd its task. The general commands:

```bash
#Gerneral:
# Iperf-server
iperf -s -i 0.5 -N -p 2622

#Iperf-client
iperf -c bones.informatik.uni-osnabrueck.de -i 0.5 -p 2622 -N -n 16MB

# -i for updat intervall
# -N to disale Nagle's Algorithm (Package buffering)
# -n size of files to transmit
# -p Port
```
I also captured the data (no payload only header) between the iperf instances with tcpdump:
```bash
#capture
sudo tcpdump -s 96 -n -e -i eth0 -w evaluation.pcap port 2622 or port 6622 or port 7622 or port 8622 or port 9622 or port 2222
```
To run Test run the *iperf_test.sh* file. Proxy must run with the config_iperf_bones.txt and the *-t* flag

**Restrictions:**
No bidirectiona because it needs reverse route and that does not work if client is behind NAT. iperf3 fixes that.

## Questions
*NONE*