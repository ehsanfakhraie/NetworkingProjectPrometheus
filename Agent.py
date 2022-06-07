import datetime
import socket
import threading
import time
from abc import ABC, abstractmethod

HOST = '127.0.0.1'
PORT = 8686


# Main agent class with basic functionalities
class Agent:
    socket = None
    # name of agent
    name = ''
    # time interval to send data
    interval = 0

    def __init__(self):
        self.initial_socket()

    def initial_socket(self):
        """
            Initialize socket object
            :return: Void
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, PORT))

    @abstractmethod
    def get_data(self):
        """
            Abstract method for system information retrieval
            To be implemented for different agents
        """
        pass

    def data_to_binary(self, data):
        """
        Convert data to binary format
        :param data: data to be converted
        :return: binary data
        """
        return data.encode('utf-8')

    def send_data(self):
        """
        Send data received from get_data function via socket
        :return: Void
        """
        self.socket.sendall(self.data_to_binary(self.get_data()))

    def agent_service(self):
        """
        background task for agent
        :return: Void
        """
        self.log(f"Starting agent {self.name}")
        while True:
            self.send_data()
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


# run test agent
if __name__ == '__main__':
    test_agent = TestAgent("Test Agent 1")
    test_agent.start_agent()

    test_agent = TestAgent("Test Agent 2")
    test_agent.start_agent()
