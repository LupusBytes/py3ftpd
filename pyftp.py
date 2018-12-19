import threading
from client import Client
from ftpcommands import *
from network import *

# Get settings from config.ini, read the config file comments for a detailed description on each value
config = configparser.ConfigParser()
config.read('config.ini')

host = config['IP']['Host']
port = int(config['IP']['Port'])

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


def client_thread(client):
    welcome_msg = "220 (PyFTP 0.0.1)"
    client.connection.send((welcome_msg + "\r\n").encode())
    keep_alive = True
    while keep_alive:
        command = client.connection.recv(1024).decode()
        print("Received from " + client.address[0] + ":" + str(client.address[1]) + " ... " + command)
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


def accept_connections():
    conn, addr = create_command_socket(host, port).accept()
    client = Client(conn, addr)
    t = threading.Thread(target=client_thread, args=(client,))
    t.start()


def main():
    print("Started FTP server on port", str(port) + ", listening on", host)
    while True:
        accept_connections()


if __name__ == "__main__":
    main()
