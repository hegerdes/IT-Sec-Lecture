import time
import gnupg
import socket

HOST = '127.0.0.1'
PORT = 4711

# Nice formatting
RED='\033[1;31m'
GRN='\033[1;32m'
YEL='\033[1;33m'
BLU='\033[1;34m'
GRY='\033[1;90m'
NC='\033[0m' # No Color


class GPG_Messenger:

    def __init__(self, path=None, port=4711, host='127.0.0.1'):
        self.host = host
        self.port = port
        self.path = path
        self.gpg = gnupg.GPG()
        self.gpg.encoding = 'utf-8'
        self.p_keys = self.gpg.list_keys(True)
        self.private = None
        self.conn = None
        self.public_keys = self.gpg.list_keys()


    def createConnection(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            self.conn = sock
            return sock
        except socket.error as e:
            print(RED + 'Error while opening socket.\nErrMsg: %s' % str(e) + NC + '\nSystem exit')
            exit(0)

    def getPrivateKey(self, id):
        # pw = input('Passphrase for ' + id + ': ')
        pw = 'SekII.13.MaPhBIO'
        return self.gpg.export_keys(id, True, passphrase=pw)


    def showKeys(self):
        print('Avaiable private Keys:')
        for i in range(len(self.p_keys)):
            print('(' + str(i) +'):', 'KeyID:', self.p_keys[i]['keyid'], 'uids:', self.p_keys[i]['uids'], 'fingerprint:', self.p_keys[i]['fingerprint'] )

    def selectEncyptKey(self):
        err_msg = RED + 'Invalid input!' + NC
        while True:
            print('Please select the number of the key you want to use!\nTo import a new one type "input" or "exit" for exit')
            self.showKeys()
            decison = input('What key? ')

            if decison == 'input':
                #TODO import privat
                pass
            if decison == 'exit':
                print('exit')
                exit(0)
            try:
                num = int(decison)
                if num >= len(self.p_keys) or num < 0:
                    print(err_msg)
                else:
                    self.private = self.getPrivateKey(self.p_keys[num]['keyid'])
                    return self.private
            except ValueError as e:
                print(err_msg, e)

    def runClienLoop(self):
        try:
            conn = self.createConnection()
            while True:
                user_input = input('Type your message: ')
                if(user_input == 'exit'):
                    conn.close()
                    break

                conn.sendall(user_input.encode())
                data = conn.recv(1024)
                print('Received: ', data)
        except socket.error as e:
                print(RED + 'Error while sending data.\nErrMsg: %s' % str(e))
                print(YEL + 'Trying to reconnect...' + NC)
                conn = self.createConnection()
                return (conn, False)


if __name__ == "__main__":
    henne_id = '3BBE23B367979E80'
    henne_finger = '84EC23147758B96F03A23FAD3BBE23B367979E80'

    try:
        s_msg = GPG_Messenger()
        s_msg.selectEncyptKey()
        s_msg.runClienLoop()
        # pw = input('PW')
    except KeyboardInterrupt:
        print('Interuped received. Exit')


