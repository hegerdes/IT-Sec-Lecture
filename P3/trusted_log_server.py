import socket
import gnupg


#print(gpg.list_keys())
KEY_INDEX = 1
REC_BUFFER_SIZE = 4098

class GPG_Logger:
    def __init__(self, path=None, port=4711, host='127.0.0.1'):
        self.host = host
        self.port = port
        self.path = path
        self.gpg_socket = None


        self.gpg = gnupg.GPG(use_agent=True, verbose=False)
        self.gpg.encoding = 'utf-8'
        self.private_key_list = self.gpg.list_keys(True)
        self.keyset = None

        # if len(self.gpg.list_keys(True)) == 0:
        # if True:
        #     self.createKey()
        self.getSet()
        self.createSocket()

    def getSet(self):
        self.keyset = { 'id': self.private_key_list[KEY_INDEX]['keyid'],
                        'public': self.getPublicKey(self.private_key_list[KEY_INDEX]['keyid']),
                        'private': self.getPrivateKey(self.private_key_list[KEY_INDEX]['keyid'])
                    }

    def getPrivateKey(self, id):
        return self.gpg.export_keys(id, True, passphrase='')

    def getPublicKey(self, id):
        return self.gpg.export_keys(id)


    def createKey(self):
        input_data = self.gpg.gen_key_input(key_type='RSA', key_length=2048, name_real='Trusted_logs', name_comment='gpg logger key', name_email='trustedlogs@server.com', expire_date='5y', passphrase='')
        print('Options', input_data)
        self.key = self.gpg.gen_key(input_data)
        print('key', self.key)
        # print(self.key)

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

    def runServerLoop(self):
        while True:
            try:
                conn, addr = self.gpg_socket.accept()
                print("Connection from: " + str(addr))
                data = conn.recv(REC_BUFFER_SIZE)
                while data:
                    print('data: ', data)
                    import_result = self.gpg.import_keys(data.decode())
                    print('Import', import_result.summary(), 'Fingerprints:', import_result.fingerprints)
                    conn.sendall('Echo: '.encode() + data)
                    data = conn.recv(REC_BUFFER_SIZE)
                    print('MSG', data)
                    decrypt = self.gpg.decrypt(data.decode(), always_trust=True)
                    print('decrypt', decrypt.data.decode())
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

