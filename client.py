class Client:
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        self.directory = "/"
        self.username = None
        self.data_port = None
        self.binary = True
        self.passive = False