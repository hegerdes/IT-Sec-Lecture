#!/usr/bin/python3
import asyncio
import socket

SOCKET_NUMBER = 150


# Nice formatting
RED = '\033[1;31m'
GRN = '\033[1;32m'
YEL = '\033[1;33m'
BLU = '\033[1;34m'
GRY = '\033[1;90m'
NC = '\033[0m'  # No Color

async def myCallback(reader, writer):
    # print('called', reader, writer)
    print('conn')


async def start_servers(host, port):
    server = await asyncio.start_server(myCallback, host, port)
    await server.serve_forever()


def enable_sockets():
    try:
        host = '127.0.0.1'
        port = 22324
        sockets_number = SOCKET_NUMBER
        loop = asyncio.get_event_loop()
        for i in range(sockets_number):
            loop.create_task(start_servers(host, port+i))
        loop.run_forever()
    except Exception as exc:
        print(exc)


if __name__ == "__main__":
    enable_sockets()
