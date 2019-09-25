import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
server_socket.bind(('', 10000))

while True:
    msg = server_socket.recv(1024)
    print('Got msg ' + msg.decode())





