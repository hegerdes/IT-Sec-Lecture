import socket
import gnupg


#print(gpg.list_keys())

class GPG_Logger:
    def __init__(self, path=None, port=4711, host='127.0.0.1'):
        self.host = host
        self.port = port
        self.path = path
        self.gpg_socket = None
        self.key = None

        self.gpg = gnupg.GPG()
        self.gpg.encoding = 'utf-8'

        print(self.gpg.list_keys(True))
        # if len(self.gpg.list_keys(True)) == 0:
        if True:
            self.createKey()

        #self.createSocket()

    def createKey(self):
        input_data = self.gpg.gen_key_input(key_type='RSA', key_length=2048, name_real='Trusted_logs', name_comment='gpg logger key', name_email='trustedlogs@server.com', expire_date='5y')
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
        try:
            while True:
                conn, addr = self.gpg_socket.accept()
                print("Connection from: " + str(addr))
                data = conn.recv(1024)
                while data:
                    print(data)
                    conn.sendall('Echo: '.encode() + data)
                    data = conn.recv(1024)
                print(str(addr) + " disconnected.")
        except socket.error as e:
            print('Error while opening socket: %s' % str(e))
            self.gpg_socket.close()

if __name__ == "__main__":
    try:
        logger = GPG_Logger()
        # logger.runServerLoop()
    except KeyboardInterrupt:
        print("Interrupt received, stopping server..")
        logger.gpg_socket.close()

