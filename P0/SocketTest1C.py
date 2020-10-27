#!/usr/bin/env python3

import socket
import pickle
import requests
import shutil
import os

# NOTE: This script will use pickle caching for answers
# PW: https://sys.cs.uos.de/lehre/its/2020/sphinx_answer.png'

QA = dict()

HOST = '131.173.33.211'
PORT = 4711

if os.path.isfile('QA_cache.pickle'):
    QA = pickle.load(open("QA_cache.pickle", "rb"))
    print(QA)

start_msg = "Hello Sphinx!"
mat_nr = "123456"

# QA = {
#     b'What is the name of the vulnerability linked to SSL heartbeats?': 'heartbleed',
#     b'Which port is normally used for HTTPS requests?': '443',
#     b'Which C-function can be used to convert a port from host byte order to network byte oder?': 'htons',
#     b'What is not only a James Bond film, but also a vulnerability that is harder to exploit and mitigate than Meltdown?': 'spectre',
#     b'What is my IPv4 address (XXX.XXX.XXX.XXX)?': '131.173.33.211',
#     b'What does DNS stand for?': 'domain name system',
#     b'Where is The Great Firewall to be found?': 'china',
#     b'Which OSI-layer are routers normally associated with (number)?': '3',
#     b'What is the reliable, connection-oriented transport protocol called (abbreviation)?': 'tcp',
#     b'What kind of attack is TCP SYN flooding (abbreviation)?': 'dos'}


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("Sending: " + start_msg)
    s.sendall(str.encode(start_msg))
    data = s.recv(1024)
    print('Received: ', repr(data))
    print("Sending: " + mat_nr)
    s.sendall(str.encode(mat_nr))
    data = s.recv(1024)
    print('Received: ', repr(data))
    for i in range(5):
        if "The password is" in data.decode():
            print()
            res = requests.get(data.decode()[17:], stream=True)
            out_path = os.path.dirname(
                os.path.abspath(__file__)) + "/pw_pic.png"
            with open(out_path, "wb") as outfile:
                shutil.copyfileobj(res.raw, outfile)
            print("PW picture saved to: " + out_path)
            break
        if data in QA:
            print("Answer is chached: " + QA[data])
            s.sendall(str.encode(QA[data]))
            data = s.recv(1024)
            print('Received: ', repr(data))
        else:
            text = input("Enter answer: ")
            QA[data] = text

pickle.dump(QA, open("QA_cache.pickle", "wb"))
