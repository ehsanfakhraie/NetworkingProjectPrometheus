import datetime
import json
import socket
import threading
import time
from abc import ABC, abstractmethod
from prometheus_client import start_http_server, Summary, Gauge, Counter, Histogram

HOST = '127.0.0.1'
PORT = 8686


class Client:
    """
    Class for storing client data including name, data type, prometheus_client object, conn
    """

    def __init__(self, initial_data, conn, addr):
        self.name = initial_data['name']
        self.data_type = initial_data['type']
        self.conn = conn
        self.addr = addr

        if self.data_type == 'gauge':
            self.prometheus_client = Gauge(self.name, 'description')
        elif self.data_type == 'counter':
            self.prometheus_client = Counter(self.name, 'description')
        elif self.data_type == 'histogram':
            self.prometheus_client = Histogram(self.name, 'description')
        elif self.data_type == 'summary':
            self.prometheus_client = Summary(self.name, 'description')

    def handel_received_data(self, data):
        """
        Handel received data
        :param data: data to be handeled
        :return: Void
        """
        if data['type'] == 'gauge':
            self.prometheus_client.set(data['data']['value'])
        elif data['type'] == 'counter':
            self.prometheus_client.inc(data['data']['value'])
        elif data['type'] == 'histogram':
            self.prometheus_client.observe(data['data']['value'])
        elif data['type'] == 'summary':
            self.prometheus_client.observe(data['data']['value'])


class Server:
    """
    Class for server receiving data from agents
    """
    socket = None

    # list of clients connected to server
    clients = []

    def __init__(self):
        self.name = "Server"
        self.addr = None
        self.conn = None
        self.initial_socket()

    def initial_socket(self):
        """
            Initialize socket object
            :return: Void
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))

    def run_server(self):
        """
        Run server as a service
        :return: Void
        """
        self.socket.listen(5)
        while True:
            # accept connection from client and create a thread for it
            self.conn, self.addr = self.socket.accept()
            # get initial data from client
            initial_data = json.loads(self.conn.recv(1024).decode('utf-8'))

            # create client object
            client = Client(initial_data, self.conn, self.addr)
            # add client to list of clients
            self.clients.append(client)

            # log initial data
            self.log(f"Received initial data from {self.addr}: {initial_data}")

            self.log(f"Client {self.addr} connected")

            threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client):
        """
        Handle client connection
        :param conn: client connection
        :param addr: client address
        :return: Void
        """
        while True:
            try:
                data = client.conn.recv(1024)
            except ConnectionResetError:
                self.log(f"Client {client.addr} disconnected")
                self.clients.remove(client.conn)
                break
            if not data:
                break
            self.log(f"Received data from {client.addr}: {data.decode('utf-8')}")
            client.handel_received_data(json.loads(data.decode('utf-8')))

    def log(self, message, type='info'):
        """
        Log given message with a specific format including system data and time
        :param message: message to be logged
        :param type: info, warning, error
        """

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if type == 'info':
            print(f"[INFO][{timestamp}]  {self.name} : {message}")
        elif type == 'warning':
            print(f"[WARNING][{timestamp}]  {self.name} : {message}")
        elif type == 'error':
            print(f"[ERROR][{timestamp}]  {self.name} : {message}")


# Run server
start_http_server(8000)
server = Server()
server.run_server()
