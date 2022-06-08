import datetime
import socket
import threading
import time
from abc import ABC, abstractmethod

HOST = '127.0.0.1'
PORT = 8686


# Class for server receiving data from agents
class Server:
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
            self.clients.append(self.conn)
            self.log(f"Client {self.addr} connected")
            threading.Thread(target=self.handle_client, args=(self.conn, self.addr)).start()

    def handle_client(self, conn, addr):
        """
        Handle client connection
        :param conn: client connection
        :param addr: client address
        :return: Void
        """
        while True:
            try:
                data = conn.recv(1024)
            except ConnectionResetError:
                self.log(f"Client {addr} disconnected")
                self.clients.remove(conn)
                break
            if not data:
                break
            self.log(f"Received data from {addr}: {data.decode('utf-8')}")

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
server = Server()
server.run_server()
