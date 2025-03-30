from socket import socket
from logging import error

from src.http.parser import Parser, EmptySocketException
from src.http.response import Response
from src.core.uriDispatcher import URI_Dispatcher
from src.dao.dao import DAO

class ThreadService:

    def __init__(self, sock : socket, dispatcher : URI_Dispatcher, dao : DAO) -> None:
        
        try:
            parser = Parser(sock)
            response = dispatcher.dispatch(parser,dao)
            #print(response.bytes())
            sock.send(response.bytes())
            sock.close()

        except EmptySocketException:

            sock.close()

        except Exception as exc:

            error(exc,exc_info=True)
            response = Response(500)
            sock.send(response.bytes())
            sock.close()
        
