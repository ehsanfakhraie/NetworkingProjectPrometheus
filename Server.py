import datetime
import json
import socket
import threading
import time
from abc import ABC, abstractmethod
from prometheus_client import start_http_server, Summary, Gauge, Counter, Histogram

HOST = '127.0.0.1'
PORT = 8686

# Defalut metrics
# CPU count
cpu_count = Gauge('cpu_count', 'CPU count', ['agent_name'])
# CPU usage
cpu_usage = Gauge('cpu_usage', 'CPU usage', ['agent_name'])
# memory usage
memory_usage = Gauge('memory_usage', 'Memory usage', ['agent_name'])
# disk usage
disk_usage = Gauge('disk_usage', 'Disk usage', ['agent_name'])


class Client:
    """
    Class for storing client data including name, data type, prometheus_client object, conn
    """

    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr

    def handel_received_data(self, data):
        """
        Handel received data
        :param data: data to be handeled
        :return: void
        """
        raw_data = data['data']
        agent_name = data['name']
        hostname = raw_data['hostname']
        cpu_count.labels(f"{agent_name}:{hostname}").set(raw_data['cpu_count'])
        cpu_usage.labels(f"{agent_name}:{hostname}").set(raw_data['cpu_percent'])
        memory_usage.labels(f"{agent_name}:{hostname}").set(raw_data['memory_percent'])
        disk_usage.labels(f"{agent_name}:{hostname}").set(raw_data['disk_percent'])


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
            client = Client(self.conn, self.addr)
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
                self.clients.remove(client)
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
