# #!/usr/bin/env python
#
# from pyftpdlib import servers
# from pyftpdlib.handlers import FTPHandler
# address = ("0.0.0.0", 21)  # listen on every IP on my machine on port 21
# server = servers.FTPServer(address, FTPHandler)
# server.serve_forever()


import os

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import itertools

authorizer = DummyAuthorizer()

# Define a new user having full r/w permissions and a read-only
# anonymous user

N_PLAYERS = 5
N_ARDUINOS = 3

for n_player, n_arduino in itertools.product(range(N_PLAYERS), range(N_ARDUINOS)):
    username = f'player_{n_player}_arduino_{n_arduino}'
    password = 'thepassword'
    authorizer.add_user(username, password, homedir='/Users/asm/Projects/AffectiveComputingDKFI/Data', perm='elradfmwMT')

# authorizer.add_anonymous(os.getcwd())

# Instantiate FTP handler class
handler = FTPHandler
handler.authorizer = authorizer

# Define a customized banner (string returned when client connects)
handler.banner = "pyftpdlib based ftpd ready."

# Specify a masquerade address and the range of ports to use for
# passive connections.  Decomment in case you're behind a NAT.
# handler.masquerade_address = '151.25.42.11'
# handler.passive_ports = range(60000, 65535)

# Instantiate FTP server class and listen on 0.0.0.0:2121
address = ('', 21)
server = FTPServer(address, handler)

# set a limit for connections
server.max_cons = 256
server.max_cons_per_ip = 5

# start ftp server
server.serve_forever()

