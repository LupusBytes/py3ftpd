import configparser
from unix import *
from network import create_data_socket

# Get settings from config.ini, read the config file comments for a detailed description on each value
config = configparser.ConfigParser()
config.read('config.ini')
chroot = config['Data']['Chroot']


# AUTH - Authentication/Security Mechanism
def cmd_auth(client, command):
    # 530 Not logged in.
    return "530 Please login with USER and PASS."


# CDUP
def cmd_cdup(client, command):
    dirs = client.directory.split("/")
    del dirs[-2:-1]
    client.directory = '/'.join(dirs)
    return "250 Directory successfully changed."


# CWD
def cmd_cwd(client, command):
    next_dir = command[3:].strip()
    print("CWD debug: client_dir = " + client.directory)
    print("CWD debug: next_dir = " + next_dir)
    if next_dir == "/":
        client.directory = next_dir
    else:
        client.directory = next_dir + "/"
    return "250 Directory successfully changed."


# FEAT - Feature list implemented by the server
# RFC 2389 https://tools.ietf.org/html/rfc2389
def cmd_feat(client, command):
    return "221 No features."


# USER - Authentication username
def cmd_user(client, command):
    client.username = command[5:]
    # 331 User name okay, need password
    return "331 Please specify the password."


# LIST
def cmd_list(client, command):
    sock = create_data_socket(client)
    client.connection.send("150 connection up\r\n".encode())
    list_data = get_unix_file_list_string(chroot + client.directory)
    print("Sending list data:\n" + list_data)
    sock.send(list_data.encode())
    return "226 Directory listing sent"


# PASS - Authentication password
def cmd_pass(client, command):
    # 230 User logged in, proceed. Logged out if appropriate
    return "230 Login successful."


# PASV - Enter passive mode
def cmd_pasv(client, command):
    client.passive = True
    return "227 Entering Passive Mode."


# PORT - Specifies an address and port to which the server should connect.
def cmd_port(client, command):
    # Remove first 5 characters, strip whitespace and carriage returns and then split by comma
    numbers = command[5:].strip().split(",")

    # http://www.melvinswebstuff.com/blog/2009/04/24/calculate-ftp-data-port/
    lo = int(numbers.pop())
    hi = int(numbers.pop())
    client.data_port = hi * 256 + lo

    return "200 Data port is " + str(client.data_port)


# PWD - Print Working Directory
def cmd_pwd(client, command):
    return "257 \"" + client.directory + "\""


# RETR - Download a file
def cmd_retr(client, command):
    sock = create_data_socket(client)
    client.connection.send("150 connection up\r\n".encode())
    print("Client directory: " + client.directory)
    file_path = chroot + client.directory + command[5:].strip()
    print("Sending file: " + file_path)
    mode = 'rt'
    if (client.binary):
        mode = 'rb'
    f = open(file_path, mode)
    l = f.read(1024)
    while (l):
        sock.send(l.encode())
        l = f.read(1024)
    sock.close()
    return "226 Transfer complete."


# STOR - Upload file
def cmd_stor(client, command):
    sock = create_data_socket(client)
    filename = command[5:].strip()
    f = open(chroot + client.directory + filename, 'a')
    l = sock.recv(1024)
    while (l):
        f.write(l.decode())
        l = sock.recv(1024)
    f.close()
    sock.close()
    return "226 Transfer complete."



# SYST - Return system type
def cmd_syst(client, command):
    return "UNIX Type: L8"

# SIZE
def cmd_size(client, command):
    file_path = client.directory + command[:5]
    st = os.stat(file_path)
    return st.st_size;

# TYPE - Sets the transfer mode (ASCII/Binary).
def cmd_type(client, command):
    transfer_type = command[5:6]
    if transfer_type == "I":
        client.binary = True
    elif transfer_type == "A":
        client.binary = False
    # 200 The requested action has been successfully completed.
    return "200 Type set to " + transfer_type