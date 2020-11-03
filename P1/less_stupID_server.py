# IT Security Lecture winter 2020: Exercises
# Practical exercise 1 - dictionary attack
#
# Maintainer:           Stefanie Thieme, Till Zimmermann
# Former Maintainer:    Timmy Schüller, Dominik Diekmann, Eric Lanfer
# File Description:     Server script - TCP server receive auth requests and send error or success msgs
#                       Response codes:
#                        00: Authentication failed
#                        01: Authentication successful
#                        02: Connection refused

import socket
import base64
import hashlib as hl
import random
import time

# Remember all connected IPs
# In deplyment you would make it persistent
con_tracker = {}
# The slowdown factor and when to disconnect
SLOWDOWN = 0.1
MAX_TRYS = 100 * SLOWDOWN


def Main():
    # parameters for creating a tcp socket
    host = "127.0.0.1"
    port = 5000

    try:
        mySocket = socket.socket()
        mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mySocket.bind((host, port))
        mySocket.listen(1)
    except socket.error as e:
        print('Error while opening socket: %s' % str(e))
        exit(0)

    # TODO: Add a SALT
    msg = 'ITS202021:'.encode() + b'jdonphr7uAGOajxhCDNLzmEJwsp7GYjXDe5Uj7C/3FSxLMdf+6/jhKHapxoeA16lYHGO1Pox9At4O7oeZLVqKg=='

    print(msg)
    # receive tcp packets and check payload for correct password
    try:
        while True:
            conn, addr = mySocket.accept()
            print("Connection from: " + str(addr))

            #If you want to identify remote over IP and Port use connID = addr
            #If you want to retrict all ports on the IP use connID = addr[0]
            #connID = addr[0]
            connID = addr
            if connID not in con_tracker:
                # TODO: Log restricted IPs and reset slowdown after 6h or so.
                # Should be fine though for this task ;)
                con_tracker[connID] = 0.0
                print('Added to ' + str(connID) + ' to connection tracker')

            data = conn.recv(512)
            while data:

                # Disconnect remote if MAX_TRYS is reached
                if con_tracker[connID] > MAX_TRYS:
                    conn.close()
                    break
                # Sleep x seconds before send response. Slows brute-force down with every other try
                time.sleep(con_tracker[connID])
                # To visualize slowdown enable the print
                #print(data)

                rand = random.randint(0, 100000)
                if rand < 10:
                    conn.send('02 - Connection refused.'.encode())
                    conn.close()
                    break
                if data == msg:
                    conn.send('01 - Password correct.'.encode())
                    # Reset slowdown
                    con_tracker[connID] = 0.0
                else:
                    conn.send('00 - Password false.'.encode())

                    # Increase slowdown with every faild try
                    con_tracker[connID]+= SLOWDOWN
                data = conn.recv(512)
            print(str(addr) + " disconnected.")
    except KeyboardInterrupt:
        print("Interrupt received, stopping server...")
        mySocket.close()


if __name__ == '__main__':
    Main()
