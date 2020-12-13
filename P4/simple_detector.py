#!/usr/bin/python3
import asyncio
import socket
import sys
import datetime
import signal
import functools

MAX_SOCKETS = 5000


# Nice formatting
RED = '\033[1;31m'
GRN = '\033[1;32m'
YEL = '\033[1;33m'
BLU = '\033[1;34m'
GRY = '\033[1;90m'
NC = '\033[0m'  # No Color


class Record:

    def __init__(self, ip, ports=[]):
        self.data = {
            'ip': ip,
            'ports': ports,
            'time': datetime.datetime.now()
        }

    def addPort(self, port):
        self.data['ports'].append(port)

    def getPorts(self):
        return self.data['ports']

    def getTime(self):
        return self.data['time']

    def setTime(self, time):
        self.data['time'] = time

    def __str__(self):
        return str(self.data)



# Help MSG and usage
def printUsage():
    print('Start with ./simple_scanner.py TARGET START_PORT END_PORT')

class Detector:

    def __init__(self, host='127.0.0.1', start_port=22300, end_port=22600):
        self.host = host
        self.start_port = start_port
        self.end_port = end_port
        self.connections = dict()
        self.detections = dict()

    async def connHandler(self, reader, writer):
        c_ip, c_port = writer.get_extra_info('peername')

        # Scanner connects again
        # Maybe countermeasures? For now not activated to catch all ports the scanner scans
        # if c_ip in self.detections:
        #     return

        if not c_ip in self.connections:
            self.connections[c_ip] = Record(c_ip, [c_port])
        else:
            self.connections[c_ip].addPort(c_port)
            record = self.connections[c_ip]
            time = (datetime.datetime.now() - record.getTime()).total_seconds()
            if time < 10:
                if len(record.getPorts()) > 10:
                    #PortScannter
                    if not c_ip in self.detections:
                        print('Scan detected from IP ' + c_ip + ' in Scanned Ports ' + str(record.getPorts()) + '.')
                    self.detections[c_ip] = record
            else:
                # Time longer than 10s. Reset for this IP
                self.connections[c_ip] = Record(c_ip, [c_port])


    async def start_server(self, host, port):
        try:
            server = await asyncio.start_server(self.connHandler, host, port)
            await server.serve_forever()
        except PermissionError:
            print(RED + 'Not allowed to listen on port ' + str(port) + '. Skipping' + NC)

    def start(self,):
        try:
            self.loop = asyncio.get_event_loop()
            # self.loop.add_signal_handler(signal.SIGHUP, functools.partial(self.close, self.loop))
            # self.loop.add_signal_handler(signal.SIGTERM, functools.partial(self.close, self.loop))
            step = 1
            while (self.end_port - self.start_port)/step > MAX_SOCKETS:
                step += 1
            for i in range(self.start_port, self.end_port + 1, step):
                self.loop.create_task(self.start_server(self.host, i))
            print(GRY + 'Starting detector...' + NC)
            self.loop.run_forever()
        except Exception as exc:
            print(exc)

    def close(self, loop=None):
        try:
            for task in asyncio.all_tasks(self.loop):
                # await task.get_coro().wait_closed()
                task.cancel()
            self.loop.stop()
            self.loop.close()
        except asyncio.CancelledError:
            pass
        except:
            print('Error, Exit')
            exit(0)


if __name__ == "__main__":

    try:
        if len(sys.argv) != 3:
            printUsage()
            exit(0)

        detect = None
        start_port = int(sys.argv[1])
        end_port = int(sys.argv[2])
        # start_port = 1000
        # end_port = 1001

        if start_port >= 65535 or end_port >= 65535:
            raise ValueError('Port to big')
        if start_port < 0 or end_port < 0:
            raise ValueError('Port to small')
        if start_port > end_port:
            raise ValueError('Start port must be smaller than end port')

        detect = Detector('127.0.0.1', start_port, end_port)
        detect.start()
    except ValueError:
        print('Please provide a valid number')
        printUsage()
        exit(0)
    except KeyboardInterrupt:
        print("Interrupt received, stopping server..")
    finally:
        # Safe shutdown
        if detect != None:  asyncio.run(detect.close())