#!/usr/bin/python3
import time
import gnupg
import socket


REC_BUFFER_SIZE = 4098
VERBOSE = False
SET_TRUST = True

# Nice formatting
RED = '\033[1;31m'
GRN = '\033[1;32m'
YEL = '\033[1;33m'
BLU = '\033[1;34m'
GRY = '\033[1;90m'
NC = '\033[0m'  # No Color


class GPG_Messenger:

    def __init__(self, path=None, port=4711, host='127.0.0.1'):
        self.host = host
        self.port = port
        self.path = path

        self.gpg = gnupg.GPG(verbose=VERBOSE)
        self.gpg.encoding = 'utf-8'
        print('Using gnupg version:', self.gpg.version)

        self.public_key_list = self.gpg.list_keys()
        self.private_key_list = self.gpg.list_keys(True)
        self.recipients = None
        self.keyset = None
        self.conn = None
        self.pw = None

    # Create Socket connection
    def createConnection(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            self.conn = sock
            return sock
        except socket.error as e:
            print(RED + 'Error while opening socket.\nErrMsg: %s' %
                  str(e) + NC + '\nSystem exit')
            raise e

    def getPrivateKey(self, id):
        out = ''
        while(out == ''):
            pw = input('Passphrase for ' + id + ': ')
            out = self.gpg.export_keys(id, True, passphrase=pw)
            print(RED + 'Coud not export. Maybe wron pw?' + NC)
        return out

    def getPublicKey(self, id):
        return self.gpg.export_keys(id)

    # Delets private and public keys
    def deletKeys(self, fp_list, pw='MySecretPW'):
        for fp in fp_list:
            print('Removing: ', fp)
            print(self.gpg.delete_keys(fp, True, passphrase=pw))
            print(self.gpg.delete_keys(fp))

    # Prints list of private keyIDs to stdout
    def showKeys(self):
        print('Avaiable private Keys:')
        for i in range(len(self.private_key_list)):
            uidstr = ['\n\t' + uid for uid in self.private_key_list[i]['uids']]
            print('(' + str(i) + '):', 'KeyID:',
                  self.private_key_list[i]['keyid'], 'Fingerprint:', self.private_key_list[i]['fingerprint'], 'uids:', ''.join(uidstr))

    # Handls the initial key exchange
    def initConn(self):
        conn = self.createConnection()
        # Send key
        conn.sendall(self.keyset['public'].encode())

        # Receive key
        data = conn.recv(REC_BUFFER_SIZE)
        import_result = self.gpg.import_keys(data.decode())
        print('Imported:', import_result.summary(),
              'Fingerprints:', import_result.fingerprints)

        # Import check
        for res in import_result.results:
            if(res['fingerprint'] == None or res['text'] == 'No valid data found'):
                print(
                    RED + 'Error while importing keys. Please make sure to provide a valid key' + NC)
                raise Exception('Import error')

        # Set TrustLevel
        if(SET_TRUST):
            self.gpg.trust_keys(import_result.fingerprints, 'TRUST_ULTIMATE')

        # Update pub_key_list
        self.public_key_list = self.gpg.list_keys()
        self.recipients = import_result.fingerprints
        print('Recipients are:', self.recipients)
        return conn

    # User input to select what key to use
    def selectEncyptKey(self):
        err_msg = RED + 'Invalid input!' + NC
        while True:
            print('Please select the number of the key you want to use!\nTo import a new one type "inport" or "exit" for exit')
            self.showKeys()
            decison = input('What key? ')

            if decison == 'inport':
                # TODO import privat
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
                                   "fingerprint": self.private_key_list[num]['fingerprint'],
                                   'public': self.getPublicKey(self.private_key_list[num]['keyid']),

                                   # If you want the private key in memory enable this. NOT the best idea
                                   # 'private': self.getPrivateKey(self.private_key_list[num]['keyid'])
                                   }
                    return self.keyset
            except ValueError as e:
                print(err_msg + ' ErrMSG:', e)

    # Sends encryped and signed msg to server using a tcp socket
    def sendMSG(self, conn):
        try:
            # Get msg
            user_input = input('Type your message: ')
            if(user_input == 'exit'):
                conn.close()
                return (conn, 'exit')
            print('Sending to:', self.recipients)

            # Encryp and sign
            encryped = None
            if self.pw == None:
                encryped = self.gpg.encrypt(
                    user_input, self.recipients, sign=self.keyset['fingerprint'])
            else:
                encryped = self.gpg.encrypt(
                    user_input, self.recipients, sign=self.keyset['fingerprint'], passphrase=self.pw)

            if(not encryped.ok):
                print(
                    RED + 'Err while encrypting. Please try again and check key config or add pw:\n' + encryped.status + NC)
                self.pw = input('Enter passphrase: ')
                return (conn, 'conuinue')

            # Send
            conn.sendall(encryped.data)
            data = conn.recv(REC_BUFFER_SIZE).decode()

            # Empty recv. Try send again. Maybe socket was reset
            if data == '':
                print(YEL + 'Empty server result. Try again.' + NC)
                return(conn, 'conuinue')

            # Check rev status
            if data == 'UNTRUSTED' or data == 'ERROR':
                print(RED + 'Received: ' + data + NC)
                print('Secure and unambiguous communication is not gurenteed. Exit...')
                conn.close()
                return (conn, 'exit')
            else:
                print(GRN + 'Received: ' + data + NC)
                return (conn, 'conuinue')

        except socket.error as e:
            print(RED + 'Error while sending data.\nErrMsg: %s' % str(e))
            print(YEL + 'Trying to reconnect...' + NC)
            # Reconnect and key exchange
            conn = self.initConn()
            return (conn, 'conuinue')

    def runClienLoop(self):
        # Send key
        conn = self.initConn()

        # MSG loop
        while True:
            conn, status = self.sendMSG(conn)
            if status == 'exit':
                conn.close()
                break
            if status == 'conuinue':
                pass


if __name__ == "__main__":

    try:
        s_msg = GPG_Messenger()
        s_msg.selectEncyptKey()
        s_msg.runClienLoop()
    except KeyboardInterrupt:
        print('Interuped received. Exit')
    except:
        print('Something wrong')
        exit(0)

        # Delet all trustedlogs@server.com keys
        # fp = []
        # for key in s_msg.public_key_list:
        #     if('trustedlogs@server.com' in key['uids'][0]): fp.append(key['fingerprint'])
        # s_msg.deletKeys(fp)

        # Delet all privat and its public key, excep my onw
        # fp = []
        # for key in s_msg.private_key_list:
        #     if(key[''] == '84EC23147758B96F03A23FAD3BBE23B367979E80'): continue
        #     fp.append(key['fingerprint'])
        # s_msg.deletKeys(fp)
