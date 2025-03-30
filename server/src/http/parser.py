from socket import socket
from io import BytesIO
from re import search
from json import loads
from urllib.parse import unquote

class EmptySocketException(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class Parser:

    def __init__(self, sock : socket) -> None:
        
        self.__socket = sock

        self.__method : str = ""
        self.__uri : str = ""
        self.__version : str = ""
        self.__headers : dict[str,str] = {}
        self.__body : str | bytes | dict | list | None = None

        first_line = self.__readLine()
        

        matches = search(r"(?P<method>\w+)\s(?P<uri>/.*)\s(?P<version>HTTP/\d\.\d)",first_line)

        self.__method = matches[1]
        self.__uri = matches[2]
        self.__version = matches[3]

        while (line := self.__readLine()) != "":

            matches = search(r"(?P<key>.+):\s(?P<value>.+)",line)
            self.__headers[matches[1]] = matches[2]

        if (content_length := self.__headers.get("Content-Length")) is not None and (length := int(content_length)) > 0:

            body = self.__readBody(length)

            content_type = self.__headers["Content-Type"]

            match content_type:

                case "text/plain" | "application/javascript" | "text/html" | "application/xml":

                    self.__body = body.decode()
            
                case "application/json":

                    self.__body = loads(body)

                case "application/x-www-form-urlencoded":

                    self.__body = {}
                    form_data = str(unquote(body)).split("&")
                    
                    for data in form_data:

                        matches = search(r"(?P<key>.+)=(?P<value>.+)",data)
                        self.__body[matches[1]] = matches[2]

                case content_type if content_type.startswith("multipart"):

                    self.__body = {}

                    matches = search(r"boundary=(?P<boundary>-+\w+)",content_type)

                    boundary = matches[1]

                    form_data = body.split("--".encode() + boundary.encode())

                    for data in form_data:

                        data = data.strip()

                        if data.startswith("Content-Disposition".encode()):

                            matches = search(r"name=\"(?P<name>\w+)\"\r?\n\r?\n(?P<text>(\w+\s?)+)".encode(),data)
                            
                            if matches is not None:

                                self.__body[matches[1].decode()] = matches[2].decode()

                            else:

                                matches = search(r"name=\"(?P<name>\w+)\";\sfilename=\"(?P<filename>\w+\.\w+)\"\r?\nContent-Type:\s(?P<type>\w+/\w+\r?\n\r?\n)".encode(),data)
                                file = data[matches.span()[1]:]
                                self.__body[matches[1].decode()] = [matches[2].decode(),matches[3].decode().strip(),file]




    @property
    def method(self) -> str:

        return self.__method
    
    @property
    def uri(self) -> str:

        return self.__uri
    
    @property
    def version(self) -> str:

        return self.__version
    
    @property
    def headers(self) -> dict[str,str]:

        return self.__headers
    
    @property
    def body(self) -> str | bytes | list | dict | None:

        return self.__body

    def __readLine(self) -> str:

        first_character = self.__socket.recv(1)

        match len(first_character) == 0:

            case True:
                
                raise EmptySocketException()

            case False:

                buffer = BytesIO()

                while True:

                    buffer.write(self.__socket.recv(1))
                    buffer.seek(0)

                    for byte in buffer:

                        if byte.endswith("\n".encode()):

                            return (first_character + byte).decode().strip()

                    
    def __readBody(self, length : int) -> bytes:

        body = bytes()
        
        while len(body) != length:

            body = body + self.__socket.recv(4092)

        return body