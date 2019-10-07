from threading import Thread
import socket
from _datetime import datetime
from queue import Queue
import time
import select

SLEEP_TIME = 0.001

class PlayerArduinoPortConverter:

    def __init__(self):
        pass

    def get_player_arduino2port_converter(self):
        def player_arduino2port(player_id, arduino_id):
            port = 10000 + 10 * arduino_id + player_id
            return port

        return player_arduino2port

    def get_port2player_arduino_converter(self):
        def port2player_arduino(port):
            player_id = port % 10
            arduino_id = (port % 100) // 10

            return player_id, arduino_id

        return port2player_arduino


class SocketThread(Thread):

    def __init__(self, port, name=None):
        super().__init__()

        # self.port = player_arduino2port(player_id, arduino_id)
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.bind(('', self.port))
        # self.socket.settimeout(0.5)
        # self.socket.setblocking(0)
        # self.socket.shutdown()

        if name is None:
            self.name = str(self.port)
        else:
            self.name = name


class ListeningThread(SocketThread):

    def __init__(self, queue, *args, verbose=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.queue = queue
        self.verbose = verbose
        self.closed = False
        # self.socket.settimeout(0.5)  # In order to don't block the process. Exceptions then must be handled

    def run(self):
        print('Thread ' + self.name + ' are listening...')
        while not self.closed:
            ready, _, _ = select.select([self.socket], [], [], SLEEP_TIME)

            if not ready:
                time.sleep(SLEEP_TIME)
                continue

            msg, addr = self.socket.recvfrom(1024)  # buffer size is 1024 bytes

            if self.verbose:
                print("received message:", msg)
                print("sender:", addr)

            msg = msg.decode()
            msg_timestamp = datetime.timestamp(datetime.now())

            msg_parts = msg.split(': ')
            if len(msg_parts) == 1:
                continue

            msg_type = msg_parts[0]
            msg_content = msg_parts[1]

            queue_item2add = {
                'msg_type': msg_type,
                'msg_content': msg_content,
                'msg_timestamp': msg_timestamp,
                'device_name': self.name,
                'receiving_port': self.port,
            }

            self.queue.put(queue_item2add)


class SendingThread(SocketThread):

    def __init__(self, address, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.address = address

    def send(self, msg):
        self.socket.sendto(msg.encode(), self.address)


class PeriodicSendingThread(SendingThread):

    def __init__(self, *args, msg, period=0.2, **kwargs):
        super().__init__(*args, **kwargs)

        self.period = period
        self.msg = msg
        self.send = False
        self.closed = False

    def run(self):
        while not self.closed:
            if self.send:
                self.socket.sendto(self.msg.encode(), self.address)
                time.sleep(self.period)
            else:
                # time.sleep(self.period)
                time.sleep(SLEEP_TIME)

    def start_periodic_send(self):
        self.send = True

    def stop_periodic_send(self):
        self.send = False



















