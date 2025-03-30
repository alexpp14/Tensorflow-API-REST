from src.core.server import Server
from json import loads


with open("config.json") as reader:

    config = reader.read()

configuration : dict = loads(config)


host = configuration.get("host")
port = configuration.get("port")
workers = configuration.get("workers")    

server = Server(hostname=host,port=port,workers=workers)
server.start()
server.join()

