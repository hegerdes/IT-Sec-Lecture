# Final Task ITS

## Task 1
### Task 1.1
All reusable code can be found in *ProxyParser* and *BaseProxy*.

### Task 1.2
```bash
# SSH Tunnel with ssh comand
ssh -L 127.0.0.1:8000:icanhazip.com:80 my_user@bones.informatik.uni-osnabrueck.de -p 22 -N
```
This command gets wrapped in a python subprocess call.

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

### Task 2.2
```bash
# Server cert

#Does not work -_-
openssl req -new -newkey rsa:2048 -nodes -keyout test.key -days 3650 -batch -subj "/CN=server-969272/C=DE/ST=LowerSaxony/L=Osnabrueck/O=UNI/OU=Student/emailAddress=hegerdes@uos.de" -reqexts SAN -config <(cat /etc/ssl/openssl.cnf <(printf "\n[SAN]\nsubjectAltName=DNS:localhost,DNS:bones.informatik.uni-osnabrueck.de,DNS:diggory.informatik.uni-osnabrueck.de,IP:127.0.0.1,IP:131.173.33.209,IP:131.173.33.211")) -out test.csr

# So use conf file
openssl req -new -newkey rsa:2048 -nodes -keyout test.key -days 365 -batch -out test.csr -config openssl.conf -subj "/CN=server-969272/C=DE/ST=LowerSaxony/L=Osnabrueck/O=UNI/OU=Student/emailAddress=hegerdes@uos.de"

#sign
openssl x509 -req -days 365 -in test.csr -CA ca.pem -CAkey ca.key -CAcreateserial -set_serial 01 -out test.pem
```
**Conf file for openssl (Server, Client)**
```Conf
[ req ]
default_bits       = 2048
distinguished_name = req_distinguished_name
req_extensions     = req_ext

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

[ req_ext ]
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


---
## Task 3


---
## Questions
### Task 1
 * Retry logic?
 * Webbrowser creates multible requests
 * How long should connection stay open

### Task 2
 * What encryption to use? Key size
 * Script should automake all keys and certs?
 * libs or subprosess allowed?

