# Final Task ITS

## Task 1
```bash
# SSH Tunnel with ssh comand
ssh -L 127.0.0.1:8000:icanhazip.com:80 my_user@bones.informatik.uni-osnabrueck.de -p 22
```

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

