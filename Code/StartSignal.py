import socket
import sys
import time
from datetime import datetime

TIME_FORMAT4FILES = '%Y-%m-%d-%H-%M-%S'

datetime_start = datetime.now().strftime(TIME_FORMAT4FILES)

time.sleep(2)

# msg = bytes('end'.encode())
# new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
new_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
new_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
new_socket.bind(('', 4000))

msg = bytes('start'.encode())
new_socket.sendto(msg, ('192.168.31.255', 3000))

time.sleep(20)

msg = bytes('end'.encode())
new_socket.sendto(msg, ('192.168.31.255', 3000))

time.sleep(2)

# datetime_start = '2019-09-24-14-30-00'
datetime_end = '2019-10-01-00-00-00'
msg = bytes(f'upload {datetime_start} {datetime_end}'.encode())
new_socket.sendto(msg, ('192.168.31.255', 3000))



# msg = bytes('status'.encode())
# new_socket.sendto(msg, ('192.168.31.255', 3000))


msg = bytes('time_sync'.encode())
new_socket.sendto(msg, ('192.168.31.255', 3000))







# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server_address = ('', 4002)
# sock.bind(server_address)
# sock.connect(('192.168.31.206', 3000))
# opponent_address = ('255.255.255.255', 3000)
# # sock.sendto(opponent_address)
# msg = bytes('start'.encode())
# sock.send(msg)
# sock.sendto(msg, opponent_address)
# sock.connect(('0.0.0.0', 3000))
# sock.connect(opponent_address)



client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.bind(("", 37020))
client.sendto(msg, ('<broadcast>', 3000))
client.sendto(msg, ('255.255.255.255', 3000))
client.sendto(msg, ('192.168.31.206', 3000))





# new_socket.sendto(msg, ('192.168.0.255', 4002))


new_socket.sendto(msg, ('192.168.31.206', 3000))
new_socket.connect(('192.168.31.206', 3000))
new_socket.send(msg)






def send_command(command):
    command_encoded = bytes(command.encode())
    print(command_encoded)
    sock.send(command_encoded)
    time.sleep(1)
    # sock.close()


send_command('start')
send_command('end')
send_command('status')



sock.sendall(b'start')




sock.connect(("www.python.org", 80))



socket.gethostname()


sock.listen()



new_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
if ip == '':
    new_socket.bind((ip, port))

sock = socket.create_connection(('localhost', 10002))


