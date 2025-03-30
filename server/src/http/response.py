from json import dumps

from src.http.HTTPcodes import HTTPCode

class Response:

    def __init__(self, code : int = 200, version : str = "HTTP/1.1", headers : dict[str,str] = {}, body : str | bytes | list | dict | tuple | None = None ) -> None:
        
        codes = HTTPCode()
        code, code_text = codes.code(code)

        self.__bytes = (version + " " + str(code) + " " + code_text + "\n").encode()

        for key, value in headers.items():

            self.__bytes = self.__bytes + (key + ": " + value + "\n").encode()

        self.__bytes = self.__bytes + "\n".encode()

        if body is not None:

            match body:

                case str():

                    self.__bytes = self.__bytes + body.encode()

                case bytes():

                    self.__bytes = self.__bytes + body

                case list() | dict() | tuple():

                    self.__bytes = self.__bytes + dumps(body).encode()

    def bytes(self) -> bytes:

        return self.__bytes