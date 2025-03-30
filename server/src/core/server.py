from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from socket import socket, AF_INET6

from src.core.threadService import ThreadService
from src.core.uriDispatcher import URI_Dispatcher
from src.dao.dao import DAO

class Server(Thread):

    def __init__(self, hostname : str = "::1", port : int = 9999, workers : int = 12) -> None:
        super().__init__()

        self.__socket = socket(AF_INET6)
        self.__socket.bind((hostname,port))
        self.__pool = ThreadPoolExecutor(workers)
        self.__dispatcher = URI_Dispatcher()
        self.__dao = DAO()

    def run(self) -> None:

        self.__socket.listen()
        
        while True:
            client, addr = self.__socket.accept()
            self.__pool.submit(ThreadService(client,self.__dispatcher,self.__dao))
        

        