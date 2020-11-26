import time
import gnupg
import socket


REC_BUFFER_SIZE = 4098

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
        self.public_key_list = self.gpg.list_keys()
        self.private_key_list = self.gpg.list_keys(True)
        self.keyset = None
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

    def getPublicKey(self, id):
        return self.gpg.export_keys(id)

    def showKeys(self):
        print('Avaiable private Keys:')
        for i in range(len(self.private_key_list)):
            print('(' + str(i) +'):', 'KeyID:', self.private_key_list[i]['keyid'], 'uids:', self.private_key_list[i]['uids'], 'fingerprint:', self.private_key_list[i]['fingerprint'] )

    def initConn(self):
        recipients = ['DF83C56A54A7D878422EFDF1274E3DEF15E41CB1']
        conn = self.createConnection()
        conn.sendall(self.keyset['public'].encode())
        data = conn.recv(REC_BUFFER_SIZE)
        import_result = self.gpg.import_keys(data.decode())
        print('Import', import_result.summary(), 'Fingerprints:', import_result.fingerprints)
        conn.sendall(self.gpg.encrypt('Hello', recipients).data)
        conn.close()

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
                if num >= len(self.private_key_list) or num < 0:
                    print(err_msg)
                else:
                    self.keyset = {'id': self.private_key_list[num]['keyid'],
                                    'public': self.getPublicKey(self.private_key_list[num]['keyid']),
                                    'private': self.getPrivateKey(self.private_key_list[num]['keyid'])
                    }
                    return self.keyset
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
                data = conn.recv(REC_BUFFER_SIZE)
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
        # s_msg.runClienLoop()
        s_msg.initConn()
    except KeyboardInterrupt:
        print('Interuped received. Exit')


