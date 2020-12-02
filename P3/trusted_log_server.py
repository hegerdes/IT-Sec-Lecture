#!/usr/bin/python3
import socket
import gnupg


REC_BUFFER_SIZE = 4098
VERBOSE = False
SET_TRUST = True

UNTRUSTED = 'UNTRUSTED'
TRUSTED = 'TRUSTED'
ERROR = 'ERROR'

KEY_PW = 'MySecretPW'

# Nice formatting
RED = '\033[1;31m'
GRN = '\033[1;32m'
YEL = '\033[1;33m'
BLU = '\033[1;34m'
GRY = '\033[1;90m'
NC = '\033[0m'  # No Color


class GPG_Logger:
    def __init__(self, path=None, port=4711, host='127.0.0.1'):
        self.host = host
        self.port = port
        self.path = path
        self.gpg_socket = None

        # self.gpg = gnupg.GPG(use_agent=True, verbose=False, options='allow-loopback-pinentry') # Dosn't work
        self.gpg = gnupg.GPG(verbose=VERBOSE)
        self.gpg.encoding = 'utf-8'
        self.private_key_list = self.gpg.list_keys(True)
        self.public_key_list = self.gpg.list_keys()
        self.keyset = None
        self.myFingerprint = None
        print('Using gnupg version:', self.gpg.version)

        # Task does not specify what should happen if privat key exists (for eg. second start)
        # So on second server start we search for pvt key of trustedlogs@server.com
        for key in self.private_key_list:
            for uid in key['uids']:
                if 'trustedlogs@server.com' in uid:
                    print(GRY + 'Found key for trustedlogs@server.com' + NC)
                    self.myFingerprint = key['fingerprint']
                    break

        if (self.myFingerprint == None):
            print(GRY + 'No pvt key for trustedlogs@server.com found. Creating...' + NC)
            self.createKey()

        self.getKeySet()
        self.createSocket()

    # My keyset (server)
    def getKeySet(self):
        for i in range(len(self.private_key_list)):
            p_key = self.private_key_list[i]
            if p_key['fingerprint'] == self.myFingerprint:
                self.keyset = {'id': p_key['keyid'],
                               'fingerprint': p_key['fingerprint'],
                               'public': self.getPublicKey(p_key['keyid']),
                               # General not a good idea to have pvt key in memory. But did it to try womething with gnupg
                               'private': self.getPrivateKey(p_key['keyid'])
                               }
                break

    def getPrivateKey(self, id):
        return self.gpg.export_keys(id, True, passphrase=KEY_PW)

    def getPublicKey(self, id):
        return self.gpg.export_keys(id)

    def createKey(self):
        input_data = self.gpg.gen_key_input(key_type='RSA', key_length=2048, name_real='Trusted_logs',
            name_comment='gpg logger key', name_email='trustedlogs@server.com', expire_date='5y', passphrase=KEY_PW)

        genKey = self.gpg.gen_key(input_data)
        self.myFingerprint = genKey.fingerprint
        print(GRN + 'Created key with fingerprint:' + NC, self.myFingerprint)

        # Update private key list
        self.private_key_list = self.gpg.list_keys(True)

    # Socket creation
    def createSocket(self):
        try:
            mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            mySocket.bind((self.host, self.port))
            mySocket.listen(1)
            self.gpg_socket = mySocket
        except socket.error as e:
            print('Error while opening socket: %s' % str(e))
            exit(0)

    # Key exchange
    def initCrypt(self, conn):
        # Get key
        data = conn.recv(REC_BUFFER_SIZE)
        import_result = self.gpg.import_keys(data.decode())
        print('Import', import_result.summary(),
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
        print('Current client is:', import_result.fingerprints)

        # Send own key
        conn.sendall(self.keyset['public'].encode())
        return conn

    def runServerLoop(self):
        print(GRY + 'Waiting for connections...' + NC)
        while True:
            try:
                # New client
                conn, addr = self.gpg_socket.accept()
                print("Connection from: " + str(addr))

                # Key exchange
                conn = self.initCrypt(conn)
                data = conn.recv(REC_BUFFER_SIZE)
                # Read-loop
                while data:
                    decrypt = self.gpg.decrypt(
                        data.decode(), passphrase=KEY_PW)

                    # Decrypt Fail
                    if not decrypt.ok:
                        print(RED + 'Decryption fail:', decrypt.status, NC)
                        conn.sendall(ERROR.encode())

                    # Decrypt Ok, varification fail
                    if decrypt.ok and (decrypt.trust_level is None or decrypt.trust_level <= decrypt.TRUST_MARGINAL):
                        print(YEL + 'Decrypt succseeded, varification faild:',
                              decrypt.trust_text, NC)
                        conn.sendall(UNTRUSTED.encode())

                    # Decrypt ok; varifiaction ok
                    if decrypt.ok and decrypt.trust_level is not None and decrypt.trust_level > decrypt.TRUST_MARGINAL:
                        print('Decrypted_msg: ', decrypt.data.decode())
                        print('Signed by:', decrypt.username,
                              decrypt.fingerprint, decrypt.trust_level ,'Status:', GRN + TRUSTED + NC)
                        conn.sendall(TRUSTED.encode())

                    data = conn.recv(REC_BUFFER_SIZE)
                print(str(addr) + " disconnected.")
            except socket.error as e:
                print('Disconnected form: %s' % str(addr))


if __name__ == "__main__":
    try:
        logger = GPG_Logger()
        logger.runServerLoop()
    except KeyboardInterrupt:
        print("Interrupt received, stopping server..")
        logger.gpg_socket.close()
