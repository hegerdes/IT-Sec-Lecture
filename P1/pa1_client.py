import os
import socket
import hashlib as hl
import base64
import sys

to_replace = {
    'o': '0',
    'i': '1',
    'r': '2',
    'e': '3',
    'a': '4',
    's': '5',
    'g': '6',
    't': '7',
    'b': '8',
    'p': '9'}

USER = 'ITS202021:'
PORT = 5000
HOST = '127.0.0.1'


def chrReplace(word):
    for key in to_replace.keys():
        if key in word.lower():
            index = word.lower().find(key)

            # Check index with multible hits
            word = word[:index] + to_replace[key] + word[index + 1:]

    return word


def createHash(word):
    return hl.sha3_512(word.encode()).digest()


def toBase64(word):
    return base64.b64encode(word)


def createConnection():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        return s;
    except socket.error as e:
        print('Error while opening socket: %s' % str(e))
        exit(0)


def sendMsg(conn, msg):
    conn.sendall(USER.encode() + msg)
    data = conn.recv(1024)
    print('Sending: ' + USER + msg.decode())
    print('recived: ' + data.decode())
    if data == b'02 - Connection refused.':
        print('Refused connection. Restiablate it')
        conn = createConnection()
    if data == b'01 - Password correct.':
        print('Found PW: ' + msg)
        exit(0)
    return conn


if __name__ == "__main__":
    PATH = 'P1/rfc4960.txt'
    # if(len(sys.argv)!= 2):
    #     print('Plese specify dictionary!\nUsage python pa1_client.py <Path to dict>')
    #     exit(0)
    # else: PATH = sys.argv[1]
    if not os.path.isfile(PATH):
        print('File does not exist.')
        exit(0)

    b_hash = b'jdonphr7uAGOajxhCDNLzmEJwsp7GYjXDe5Uj7C/3FSxLMdf+6/jhKHapxoeA16lYHGO1Pox9At4O7oeZLVqKg=='
    print(base64.b64decode(b_hash))

    try:
        conn = createConnection()
        with open(PATH, 'r') as reader:
            s = reader.readline()
            while s != '':
                for word in s.split():
                    # print(chrReplace(word))
                    # print(word)
                    print(base64.b64decode(toBase64(createHash(chrReplace(word)))))
                    # print(toBase64(createHash(chrReplace(word))))
                    # print(toBase64(createHash(word)))
                    conn = sendMsg(conn, toBase64(createHash(chrReplace(word))))
                    # conn = sendMsg(conn, toBase64(createHash(word)))

                s = reader.readline()

    except KeyboardInterrupt:
        print("Interrupt received, stopping server..")
        conn.close()
    print('No PW found')
