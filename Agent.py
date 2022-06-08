import datetime
import json
import socket
import threading
import time
from abc import ABC, abstractmethod
from enum import Enum

HOST = '127.0.0.1'
PORT = 8686


# Main agent class with basic functionalities
class Agent:
    # type of data to be sent to server [Gauge, Counter, Histogram, Summary]
    data_type = None

    # Enum for data types
    class DataType(Enum):
        Gauge = 'gauge'
        Counter = 'counter'
        Histogram = 'histogram'
        Summary = 'summary'

    # name of agent
    name = ''

    # time interval to send data
    interval = 0

    def __init__(self):
        self.socket = None
        self.initial_socket()

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
                self.send_initial_data()
                break
            except ConnectionRefusedError:
                self.log(f"Connection refused, trying again in 5 seconds")
                time.sleep(5)

    def send_initial_data(self):
        """
        Send initial data to server
        :return: Void
        """

        self.log(f"Sending initial data to server")

        self.send_data(self.get_initial_data(), initial=True)

    def get_initial_data(self):
        """
        Get initial data to be sent to server
        :return: data to be sent
        """
        return {
            "name": self.name,
            "type": self.data_type.value,
        }

    @abstractmethod
    def get_data(self):
        """
            Abstract method for system information retrieval
            To be implemented for different agents
        """
        pass

    def format_data(self, data, initial=False):
        """
        Check if data is a dictionary and format it to a json string and binary
        :param data: data to be converted
        :return: binary data
        """
        if not isinstance(data, dict):
            raise TypeError("Data is not a dictionary")

        # data should contain name and value keys
        if 'name' not in data or 'value' not in data:
            if not initial:
                raise TypeError("Data is not in correct format")

        # Add agent name and timestamp to data
        if not initial:
            data = {
                'name': self.name,
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'data': data,
                'type': self.data_type.value
            }
        data = json.dumps(data)
        return data.encode('utf-8')

    def send_data(self, data, initial=False):
        """
        Send data received from get_data function via socket
        :return: false if data is not a dictionary
        """
        try:
            data = self.format_data(data, initial)
        except TypeError as e:
            self.log(f"Error while formatting data: {e}", 'error')
            return False

        if data is not None:
            try:
                self.socket.sendall(data)
            except ConnectionResetError:
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
            if self.send_data(self.get_data()):
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


# Test implementation of Agent class
class TestAgent(Agent):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.interval = 1

    def get_data(self):
        return f"Test data from {self.name}"


class SystemMemoryAgent(Agent):
    data_type = Agent.DataType.Gauge
    name = 'memoryssss'

    def __init__(self, name):
        super().__init__()
        self.interval = 1

    def get_data(self):
        return {"name": "memory", "value": self.get_memory_usage()}

    def get_memory_usage(self):
        import psutil
        return psutil.virtual_memory().percent


# run test agent
if __name__ == '__main__':
    system_memory_agent = SystemMemoryAgent("System Memory Agent")
    system_memory_agent.start_agent()
