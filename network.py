import socket


def create_command_socket(host, port):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(1)
    return sock


def create_data_socket(client):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to client " + client.address[0] + ":" + str(client.address[1]) + " on dataport " + str(client.data_port))
    sock.connect((client.address[0], client.data_port))
    return sock




