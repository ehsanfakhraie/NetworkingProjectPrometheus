import datetime
import json
import os
import socket
import threading
import time
from abc import ABC, abstractmethod
from enum import Enum
import psutil

HOST = '127.0.0.1'
PORT = 8686


# Main agent class with basic functionalities
class Agent:
    # name of agent
    name = ''

    # time interval to send data
    interval = 0

    def __init__(self, name, interval):
        self.socket = None
        self.initial_socket()
        self.name = name
        self.interval = interval

    def initial_socket(self):
        """
            Initialize socket object
            :return: Void
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # try to connect to server every 5 seconds
        while True:
            try:
                self.socket.connect((HOST, PORT))
                break
            except ConnectionRefusedError:
                self.log(f"Connection refused, trying again in 5 seconds")
                time.sleep(5)

    def get_system_data(self):
        """
            Get basic system data
            :return: dictionary of system data
        """
        data = {'hostname': socket.gethostname(), 'os': os.name, 'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(), 'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'network_bytes_sent': psutil.net_io_counters().bytes_sent}

        return data

    def format_data(self, data):
        """
        Check if data is a dictionary and format it to a json string and binary
        :param data: data to be converted
        :return: binary data
        """
        if not isinstance(data, dict):
            raise TypeError("Data is not a dictionary")

        # Add agent name and timestamp to data
        data = {
            'name': self.name,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'data': data,
        }
        data = json.dumps(data)
        return data.encode('utf-8')

    def send_data(self, data):
        """
        Send data received from get_data function via socket
        :return: false if data is not a dictionary
        """
        try:
            data = self.format_data(data)
        except TypeError as e:
            self.log(f"Error while formatting data: {e}", 'error')
            return False

        if data is not None:
            try:
                self.socket.sendall(data)
            except (ConnectionResetError, ConnectionAbortedError):
                self.log(f"Connection reset, trying to reconnect")
                self.initial_socket()
                self.socket.sendall(data)
            return True
        else:
            self.log(f"Data is not in correct format", 'error')
            return False

    def agent_service(self):
        """
        background task for agent
        :return: Void
        """
        self.log(f"Starting agent {self.name}")
        while True:
            if self.send_data(self.get_system_data()):
                self.log(f"Data sent to server")
            time.sleep(self.interval)

    def start_agent(self):
        """
        Start agent service in a new thread
        :return: Void
        """
        threading.Thread(target=self.agent_service).start()

    def log(self, message, type='info'):
        """
        Log given message with a specific format including system data and time and agent name

        :param message: message to be logged
        :param type: info, warning, error
        :return: void
        """

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if type == 'info':
            print(f"[INFO][{timestamp}]  {self.name} : {message}")
        elif type == 'warning':
            print(f"[WARNING][{timestamp}]  {self.name} : {message}")
        elif type == 'error':
            print(f"[ERROR][{timestamp}]  {self.name} : {message}")


# run test agent
if __name__ == '__main__':
    agent = Agent('test', 1)
    agent.start_agent()
