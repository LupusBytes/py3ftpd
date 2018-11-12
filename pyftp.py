import socket
import threading
import queue
import os
import stat
import pwd
import grp
import datetime
import time

clients = []
messages = queue.Queue()

# Setting host to 0.0.0.0 makes the FTP server bind to all available IPv4 addresses
host = "0.0.0.0"

# If port is set to 21, which is the default FTP port, we need to run the program with sudo
port = 2121

# This is the folder we are gonna present as the root of the filesystem
chroot = "/home/lupus/Projects/Python/PyFTP/data"

tcp_server_socket = socket.socket()
tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcp_server_socket.bind((host, port))
tcp_server_socket.listen(1)

clients = []


def get_unix_file_permissions_string(st, is_dir):
    # Check if directory or file
    if is_dir:
        pem_str = "d"
    else:
        pem_str = "-"

    # Get octal value of permissions of file
    pem = oct(stat.S_IMODE(st.st_mode))

    # Convert to binary
    b = bin(int(pem, 8))

    # Check if binary length is less than 11
    bit_length = b.__len__()
    if bit_length < 11:
        # Pad with zeroes on left side
        for i in range(bit_length, 11):
            b = b[:2] + "0" + b[2:]

    # Create array of read, write and execute flags
    pem_flags = ["r", "w", "x"]
    for bit in range(9):
        # If the current bit is 1, find and append the correct flag
        if b[bit + 2] == "1":
            pem_str += pem_flags[bit % 3]
        else:
            pem_str += "-"
    return pem_str


def get_last_changed_timestamp(changed_time):
    six_months_in_seconds = 15811200
    now = time.time()
    six_months_ago = now - six_months_in_seconds
    if changed_time < six_months_ago:
        return datetime.datetime.fromtimestamp(changed_time).strftime("%Y")
    return datetime.datetime.fromtimestamp(changed_time).strftime("%H:%M")


def get_posix_file_list_string(directory_path):
    directory = os.listdir(directory_path)
    file_list = ""
    for file in directory:
        # Absolute path
        file_path = directory_path + file

        # Get file status from operating system
        st = os.stat(file_path)

        # Is directory boolean
        is_dir = stat.S_ISDIR(st.st_mode)

        # Unix Permissions
        pem_string = get_unix_file_permissions_string(st, is_dir)

        # Real owner of file
        name = pwd.getpwuid(st.st_uid).pw_name

        # Real group of file
        group = grp.getgrgid(st.st_gid)[0]

        # Number of links to the inode, ST_NLINK is the 4th value of the 10-tuple returned by os.stat()
        link_count = st[3]

        # Size
        binary_size = st.st_size

        # Changed time in Unix time format
        changed_time = st[8]

        # Month when changed
        month_changed = datetime.datetime.fromtimestamp(changed_time).strftime("%b")

        # Day of month when changed
        day_of_month_changed = datetime.datetime.fromtimestamp(changed_time).strftime("%-d")

        # Either the clock as hour:minutes when last changed or the year, if more than six months ago
        timestamp = get_last_changed_timestamp(changed_time)

        file_list += ' '.join([pem_string, str(link_count), name, group, str(binary_size), month_changed,
                               day_of_month_changed, timestamp, file]) + "\r\n"
    return file_list


class Client:
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        self.directory = "/"
        self.username = None
        self.data_port = None
        self.binary = True
        self.passive = False


def create_datasocket(client):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to client " + client.address[0] + ":" + str(client.address[1]) + " on dataport " + str(client.data_port))
    sock.connect((client.address[0], client.data_port))
    return sock


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
    sock = create_datasocket(client)
    client.connection.send("150 connection up\r\n".encode())
    list_data = get_posix_file_list_string(chroot + client.directory)
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
    sock = create_datasocket(client)
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
    sock = create_datasocket(client)
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


protocol_dict = {
    "AUTH": cmd_auth,
    "CDUP": cmd_cdup,
    "CWD ": cmd_cwd,
    "FEAT": cmd_feat,
    "USER": cmd_user,
    "LIST": cmd_list,
    "PASS": cmd_pass,
    "PASV": cmd_pasv,
    "PORT": cmd_port,
    "PWD ": cmd_pwd,
    "RETR": cmd_retr,
    "STOR": cmd_stor,
    "SYST": cmd_syst,
    "TYPE": cmd_type
}


def accept_connections():
    conn, addr = tcp_server_socket.accept()
    client = Client(conn, addr)
    t = threading.Thread(target=client_thread, args=(client,))
    t.start()


def client_thread(client):
    welcome_msg = "220 (PyFTP 0.0.1)"
    client.connection.send((welcome_msg + "\r\n").encode())
    keep_alive = True
    while keep_alive:
        command = client.connection.recv(1024).decode()
        print("Recieved from " + client.address[0] + ":" + str(client.address[1]) + " ... " + command)
        method = command.strip()
        if method != "":
            while len(method) < 4:
                method += " "

            method = method[:4]
            response = protocol_dict[method](client, command)
            print("Responding to " + client.address[0] + ":" + str(client.address[1]) + " ... " + response + "\n\n\n")
            client.connection.send((response + "\r\n").encode())
        else:
            keep_alive = False

while True:
    accept_connections()
